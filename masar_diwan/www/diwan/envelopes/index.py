import frappe

from masar_diwan.permissions import require_diwan_staff
from masar_diwan.utils.portal_nav import DIWAN_PORTAL_NAV


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/diwan/envelopes"
		raise frappe.Redirect

	require_diwan_staff()

	context.no_cache = 1
	context.title = frappe._("Envelopes")
	context.lang = frappe.local.lang
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = DIWAN_PORTAL_NAV
	context.portal_section_title = "Diwan Portal"
	context.active_route = "/diwan/envelopes"

	context.envelopes = frappe.get_list(
		"Envelope",
		fields=["name", "status", "creation_date", "linked_delivery_sheet"],
		order_by="modified desc",
		limit_page_length=100,
	)
	return context
