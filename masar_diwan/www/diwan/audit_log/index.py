from urllib.parse import quote

import frappe

FILTERABLE = ["event_type", "result", "channel", "reference_doctype"]


def get_context(context):
	"""Merged into /diwan/queue?tab=audit_log (2026-09-26) - kept as a
	redirect (preserving any filter query params) so any existing bookmark/
	link to this URL still works, instead of 404ing."""
	params = "&".join(
		f"{key}={quote(frappe.form_dict[key])}" for key in FILTERABLE if frappe.form_dict.get(key)
	)
	target = "/diwan/queue?tab=audit_log"
	if params:
		target += f"&{params}"
	frappe.local.flags.redirect_location = target
	raise frappe.Redirect
