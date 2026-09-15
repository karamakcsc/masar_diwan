"""Central Access Log Entry writer.

Every place in the app that needs to record who did what - logins, document
views, downloads, QR/barcode scans, diwan tray decisions - funnels through
`log_event()` so the four summary counters and the eight report filters
(Phase 6) always see a complete, consistently-shaped picture.

Deliberately NOT wired into the core `/private/files/...` static file route:
that route is shared by every app on this bench and intercepting it would
mean monkeypatching a core Frappe request handler used well outside this
app's scope. Instead, downloads are logged at the one place we fully own:
the custom Portal download endpoint (Phase 7).
"""

import frappe
from frappe.utils import get_datetime, now_datetime


def log_event(
	event_type: str,
	result: str = "Success",
	reason: str | None = None,
	reference_doctype: str | None = None,
	reference_name: str | None = None,
	file_name: str | None = None,
	channel: str | None = None,
	user: str | None = None,
):
	user = user or frappe.session.user
	if user == "Guest":
		return None

	ip_address = getattr(frappe.local, "request_ip", None)
	device_info = None
	try:
		device_info = frappe.request.headers.get("User-Agent")
	except RuntimeError:
		pass

	if channel is None:
		channel = get_channel_for_user(user)

	is_new_ip = 0
	if ip_address:
		is_new_ip = 0 if _ip_seen_before(user, ip_address) else 1

	entry = frappe.get_doc(
		{
			"doctype": "Access Log Entry",
			"user": user,
			"event_datetime": now_datetime(),
			"event_type": event_type,
			"channel": channel,
			"result": result,
			"reason": reason,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"file_name": file_name,
			"ip_address": ip_address,
			"is_new_ip": is_new_ip,
			"device_info": device_info,
		}
	)
	# ignore_links: a denied/not-found lookup (e.g. a bogus scanned reference)
	# is itself a noteworthy event and must never be lost just because the
	# reference it points at doesn't exist.
	entry.insert(ignore_permissions=True, ignore_links=True)
	frappe.db.commit()
	return entry


def _ip_seen_before(user: str, ip_address: str) -> bool:
	return bool(
		frappe.db.exists(
			"Access Log Entry",
			{"user": user, "ip_address": ip_address},
		)
	)


def get_channel_for_user(user: str) -> str:
	user_type = frappe.db.get_value("User", user, "user_type")
	return "Portal" if user_type == "Website User" else "Desk"


def log_login(login_manager):
	log_event("Login", user=login_manager.user)


@frappe.whitelist()
def log_view(reference_doctype: str, reference_name: str, channel: str | None = None):
	allowed = frappe.has_permission(reference_doctype, "read", doc=reference_name)
	log_event(
		"View",
		result="Success" if allowed else "Denied",
		reason=None if allowed else "No read permission",
		reference_doctype=reference_doctype,
		reference_name=reference_name,
		channel=channel,
	)
	if not allowed:
		frappe.throw(frappe._("You are not permitted to view this document"), frappe.PermissionError)
