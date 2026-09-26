from urllib.parse import urlencode

import frappe


def get_context(context):
	"""Merged into /diwan/queue?tab=delivery_sheets (2026-09-26) - kept as a
	redirect so any existing bookmark/link to this URL still works, instead
	of 404ing."""
	query = {key: frappe.form_dict[key] for key in ("name", "_lang", "page", "event_type", "result", "channel", "reference_doctype") if frappe.form_dict.get(key)}
	query["tab"] = "delivery_sheets"
	frappe.local.flags.redirect_location = "/diwan/queue?" + urlencode(query)
	raise frappe.Redirect
