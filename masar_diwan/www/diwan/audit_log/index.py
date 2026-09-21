import frappe

from masar_diwan.permissions import require_diwan_staff
from masar_diwan.utils.portal_nav import DIWAN_PORTAL_NAV

FILTERABLE = ["event_type", "result", "channel", "reference_doctype"]


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/diwan/audit_log"
		raise frappe.Redirect

	require_diwan_staff()

	context.no_cache = 1
	context.title = frappe._("Access Log")
	context.lang = frappe.local.lang
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = DIWAN_PORTAL_NAV
	context.portal_section_title = "Diwan Portal"
	context.active_route = "/diwan/audit_log"

	filters = {}
	for key in FILTERABLE:
		value = frappe.form_dict.get(key)
		if value:
			filters[key] = value
	context.active_filters = filters

	# Doctype-level read/report DocPerm (Diwan Officer/Senior Management/
	# System Manager only, per the doctype's own permissions - see
	# access_log_entry.json) already gates this; nothing custom needed here,
	# same as the existing Desk "Access Log Report" this page is a portal
	# equivalent of.
	context.entries = frappe.get_list(
		"Access Log Entry",
		filters=filters,
		fields=[
			"name",
			"user",
			"event_datetime",
			"event_type",
			"channel",
			"result",
			"reason",
			"reference_doctype",
			"reference_name",
			"ip_address",
			"is_new_ip",
		],
		order_by="event_datetime desc",
		limit_page_length=200,
	)
	return context
