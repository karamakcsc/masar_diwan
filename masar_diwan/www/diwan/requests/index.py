import frappe

from masar_diwan.utils.portal_i18n import get_portal_messages

from masar_diwan.utils.portal_pagination import get_page

from masar_diwan.access_log import log_event
from masar_diwan.api.requests import get_confidentiality_levels, get_submitter_context
from masar_diwan.utils.dynamic_fields import get_dynamic_field_values_for_display
from masar_diwan.utils.portal_nav import REQUESTER_PORTAL_NAV as PORTAL_NAV

LIST_FIELDS = [
	"name",
	"request_type",
	"subject",
	"status",
	"request_date",
	"modified",
	"resulting_correspondence",
]

DETAIL_FIELDS = LIST_FIELDS + [
	"party_or_department",
	"draft_text",
	"suggested_priority",
	"suggested_confidentiality",
	"note_to_registrar",
	"decision_note",
	"owner",
]


def get_context(context):
	"""Requester Portal - merged 2026-09-26 (was /diwan/submit + /diwan/requests,
	two separate pages/routes). One URL, ?tab=submit|requests (requests is the
	default - "My Requests" is the natural landing view), so a requester no
	longer needs to know two separate bookmarks for "file something new" vs.
	"check what I already filed" - the existing side-nav/rail already just
	needed its two links pointed at this one page's two tab values (see
	portal_nav.py) rather than two separate page files."""
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/diwan/requests"
		raise frappe.Redirect

	context.no_cache = 1
	context.lang = frappe.local.lang
	context.diwan_messages = get_portal_messages()
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = PORTAL_NAV
	context.portal_section_title = "Requester Portal"

	name = frappe.form_dict.get("name")
	tab = frappe.form_dict.get("tab") or "requests"
	if tab not in ("submit", "requests"):
		tab = "requests"
	if name and tab != "submit":
		# Named requests open detail unless the submit tab explicitly requests editing.
		tab = "requests"
	context.active_tab = tab
	context.active_route = "/diwan/requests" if tab == "requests" else f"/diwan/requests?tab={tab}"

	context.detail = None

	if tab == "submit":
		if not name and not frappe.has_permission("Correspondence Request", "create"):
			frappe.throw(frappe._("You are not permitted to submit correspondence requests."), frappe.PermissionError)
		context.title = frappe._("New Correspondence Request")
		context.submitter = get_submitter_context()
		# Rendered server-side (like the rest of this page) rather than fetched
		# by the page's own JS - the list is site-configurable (see Document
		# Access Profile / Confidentiality Level), not a fixed set of 3, so the
		# radio pillgroup below is built from whatever this call returns instead
		# of 3 hardcoded options.
		context.confidentiality_levels = get_confidentiality_levels()
		context.edit_request = None
		context.edit_json = "null"
		context.existing_attachments = []
		if name:
			doc = frappe.get_doc("Correspondence Request", name)
			doc.check_permission("read")
			doc.check_permission("write")
			if doc.owner != frappe.session.user or doc.status not in ("Draft", "Needs Revision"):
				frappe.throw(frappe._("Only your own drafts and revision requests can be edited here."), frappe.PermissionError)
			editable_fields = (
				"name", "status", "request_type", "subject", "party_or_department", "draft_text",
				"suggested_priority", "suggested_confidentiality", "note_to_registrar", "decision_note",
				"correspondence_category", "correspondence_sub_category", "category_is_group",
			)
			context.edit_request = {field: doc.get(field) for field in editable_fields}
			context.edit_request.update({
				field.fieldname: doc.get(field.fieldname)
				for field in doc.meta.fields
				if field.fieldname.startswith("csf_") and field.fieldtype not in ("Section Break", "Column Break", "Tab Break")
			})
			context.edit_json = frappe.as_json(context.edit_request)
			context.title = frappe._("Edit Request")
			context.submitter = {
				"full_name": frappe.utils.get_fullname(doc.requested_by or doc.owner),
				"department": doc.requesting_department,
				"date": frappe.utils.format_date(doc.request_date or doc.creation),
			}
			context.existing_attachments = frappe.get_all("File", filters={"attached_to_doctype": doc.doctype, "attached_to_name": doc.name}, fields=["name", "file_name"])
			log_event("View", reference_doctype=doc.doctype, reference_name=doc.name, reason="Requester Portal edit")
		return context

	# tab == "requests" (default)
	if name:
		context.title = frappe._("Request {0}").format(name)
		# frappe.get_doc + has_permission (not ignore_permissions) so a
		# request belonging to someone else 404s exactly like any other
		# doctype - no separate access check needs writing here.
		if not frappe.db.exists("Correspondence Request", name):
			context.detail = {"not_found": True}
		elif not frappe.has_permission("Correspondence Request", "read", doc=name):
			context.detail = {"not_found": True}
		else:
			doc = frappe.get_doc("Correspondence Request", name)
			context.detail = {f: doc.get(f) for f in DETAIL_FIELDS}
			context.detail["not_found"] = False
			context.detail["category"] = doc.correspondence_category
			context.detail["sub_category"] = doc.correspondence_sub_category
			context.dynamic_field_values = get_dynamic_field_values_for_display(doc)
			if doc.resulting_correspondence:
				ref_no, qr_code = frappe.db.get_value(
					"Correspondence", doc.resulting_correspondence, ["reference_no", "qr_code"]
				)
				context.detail["reference_no"] = ref_no
				context.detail["qr_code"] = qr_code
			context.attachments = frappe.get_all(
				"File",
				filters={"attached_to_doctype": "Correspondence Request", "attached_to_name": name},
				fields=["name", "file_name"],
			)
			log_event(
				"View",
				reference_doctype="Correspondence Request",
				reference_name=name,
				reason="Requester Portal view",
			)
		context.detail_json = frappe.as_json(context.detail)
	else:
		context.title = frappe._("My Requests")
		# Explicit owner filter, not just permission-query scoping: a
		# DEPARTMENT_EXEMPT_ROLES user (Diwan Officer/Senior Management) has
		# unrestricted read on this doctype for the *Diwan Portal* queue, but
		# "My Requests" must always mean literally their own regardless of
		# what else their role can see - that queue is a separate page.
		context.requests = get_page(context,
			"Correspondence Request",
			filters={"owner": frappe.session.user},
			fields=LIST_FIELDS,
			order_by="modified desc",

		)

	return context
