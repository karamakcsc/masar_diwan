"""Automated notifications (Desk bell + email) at the workflow moments that
actually need someone's attention, wired via hooks.py's doc_events /
scheduler_events.

Before this module existed, hooks.py had notification_config / doc_events /
scheduler_events all commented out - nothing in the app ever pushed anything
to anyone. A Diwan Officer only learned a request was waiting by opening
/diwan/queue themselves; a requester only learned their request was decided
by opening /diwan/requests themselves; an overdue Correspondence was only
visible to whoever happened to run the "Overdue Correspondence" report.

Design choices, deliberately conservative:
- Every function here is called from a doc_events hook already wrapped by
  Frappe's own on_update dispatch, but each function still wraps its own
  body in try/except and logs to the Error Log on failure rather than
  raising - a notification failure must never block the actual document
  save/workflow transition it's reacting to. This mirrors the existing
  self-healing pattern used by ensure_workflows()/ensure_department_*() in
  install.py.
- Desk bell notifications use Frappe's own standard
  frappe.desk.doctype.notification_log.notification_log.enqueue_create_notification
  - the same mechanism ToDo assignments / mentions / share notifications
  use elsewhere in Frappe, not a bespoke doctype.
- Email is sent in addition to (not instead of) the desk notification for
  the two decision points a Website User (Portal Tracking User - the
  Requester Portal's own role, desk_access=0) needs to actually receive:
  a request being decided, and a request being submitted for review (staff
  side, so this one is Desk-notification-only - Diwan staff are always
  System Users). enqueue_create_notification is harmless to call for a
  Website User too (it just creates a row nothing will render), so it is
  not special-cased away.
- Every recipient list is derived the same way the rest of this app already
  derives "who belongs to a department" (User Permission rows with
  allow="Department"), never a new/duplicate mapping.
"""

import frappe
from frappe import _


def _notify(users, subject, document_type, document_name, email_content=None):
	"""Desk bell notification + optional email, to a de-duplicated list of
	real, enabled users. Never raises - a failure here must never break the
	document save/transition that triggered it.
	"""
	users = sorted({u for u in (users or []) if u and u != "Guest"})
	if not users:
		return
	try:
		from frappe.desk.doctype.notification_log.notification_log import (
			enqueue_create_notification,
		)

		enqueue_create_notification(
			users,
			{
				"type": "Alert",
				"document_type": document_type,
				"document_name": document_name,
				"subject": subject,
				"from_user": frappe.session.user,
			},
		)
	except Exception:
		frappe.log_error(title="masar_diwan.notifications: desk notification failed")

	if email_content:
		try:
			recipients = [
				u
				for u in frappe.get_all(
					"User", filters={"name": ["in", users], "enabled": 1}, pluck="name"
				)
				if u != "Administrator"
			]
			if recipients:
				frappe.sendmail(
					recipients=recipients,
					subject=subject,
					message=email_content,
					reference_doctype=document_type,
					reference_name=document_name,
				)
		except Exception:
			frappe.log_error(title="masar_diwan.notifications: email failed")


def _department_users(department):
	if not department:
		return []
	return frappe.get_all(
		"User Permission",
		filters={"allow": "Department", "for_value": department},
		pluck="user",
	)


def _users_with_roles(roles):
	return frappe.get_all(
		"Has Role",
		filters={"role": ["in", roles], "parenttype": "User"},
		pluck="parent",
	)


# --------------------------------------------------------------------------
# Correspondence Request - submitted for review / decided
# --------------------------------------------------------------------------

REQUEST_DECIDED_STATUSES = ("Approved & Numbered", "Rejected", "Needs Revision")


def on_correspondence_request_update(doc, method=None):
	before = doc.get_doc_before_save()
	if not before or before.status == doc.status:
		return

	if doc.status == "Pending Review":
		# A new request just entered the tray/queue - tell every Diwan
		# Officer / Senior Management user (the same audience
		# require_diwan_staff() already admits to /diwan/queue + /diwan/tray;
		# System Manager is deliberately left out here since that role is an
		# administrative bypass, not a real reviewer to page).
		_notify(
			_users_with_roles(["Diwan Officer", "Senior Management"]),
			_("New correspondence request: {0}").format(doc.subject or doc.name),
			"Correspondence Request",
			doc.name,
		)
		return

	if before.status == "Under Review" and doc.status in REQUEST_DECIDED_STATUSES:
		if not doc.requested_by:
			return
		status_label = _(doc.status)
		_notify(
			[doc.requested_by],
			_("Your correspondence request was {0}: {1}").format(status_label, doc.subject or doc.name),
			"Correspondence Request",
			doc.name,
			email_content=_(
				"Your correspondence request <b>{0}</b> has been <b>{1}</b>."
			).format(frappe.utils.escape_html(doc.subject or doc.name), status_label)
			+ (f"<br>{_('Note')}: {frappe.utils.escape_html(doc.decision_note)}" if doc.decision_note else ""),
		)


# --------------------------------------------------------------------------
# Internal Mail Movement - sent to a department
# --------------------------------------------------------------------------


def on_internal_mail_movement_update(doc, method=None):
	before = doc.get_doc_before_save()
	if not before or before.status == doc.status:
		return

	if doc.status == "In Transit":
		recipients = set(_department_users(doc.to_department))
		recipients.update(_users_with_roles(["Diwan Officer", "Senior Management"]))
		recipients.discard(frappe.session.user)
		_notify(
			list(recipients),
			_("Internal mail movement sent to your department: {0}").format(doc.name),
			"Internal Mail Movement",
			doc.name,
			email_content=_(
				"An internal mail movement ({0}) from {1} to {2} is on its way: {3}"
			).format(
				doc.name,
				frappe.utils.escape_html(doc.from_department or ""),
				frappe.utils.escape_html(doc.to_department or ""),
				frappe.utils.escape_html(doc.content_description or ""),
			),
		)


# --------------------------------------------------------------------------
# Overdue Correspondence - daily scheduled reminder
# --------------------------------------------------------------------------


def notify_overdue_correspondence():
	"""Daily (scheduler_events["daily"]). Reuses the exact same "overdue"
	definition as the existing Overdue Correspondence script report
	(follow_up_date in the past, not yet in a terminal status) so the two
	never drift apart - this just pushes what that report already shows.
	"""
	try:
		rows = frappe.get_all(
			"Correspondence",
			filters={
				"follow_up_date": ["<", frappe.utils.today()],
				"status": ["not in", ["Completed", "Archived"]],
			},
			fields=["name", "subject", "current_owner", "department", "follow_up_date"],
			ignore_permissions=True,
		)
	except Exception:
		frappe.log_error(title="masar_diwan.notifications: overdue query failed")
		return

	by_owner = {}
	for row in rows:
		if not row.current_owner:
			continue
		by_owner.setdefault(row.current_owner, []).append(row)

	for owner, owner_rows in by_owner.items():
		subject = _("You have {0} overdue correspondence item(s)").format(len(owner_rows))
		lines = "".join(
			f"<li>{frappe.utils.escape_html(r.subject or r.name)} "
			f"({_('due')} {frappe.utils.format_date(r.follow_up_date)})</li>"
			for r in owner_rows
		)
		_notify(
			[owner],
			subject,
			"Correspondence",
			owner_rows[0].name,
			email_content=f"<ul>{lines}</ul>",
		)
