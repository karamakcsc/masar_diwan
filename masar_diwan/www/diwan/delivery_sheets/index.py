import frappe

from masar_diwan.permissions import require_diwan_staff
from masar_diwan.utils.portal_nav import DIWAN_PORTAL_NAV


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/diwan/delivery_sheets"
		raise frappe.Redirect

	require_diwan_staff()

	context.no_cache = 1
	context.title = frappe._("Delivery Sheets")
	context.lang = frappe.local.lang
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = DIWAN_PORTAL_NAV
	context.portal_section_title = "Diwan Portal"
	context.active_route = "/diwan/delivery_sheets"

	# Standard frappe.get_list - Delivery Sheet's own DocPerm rows (System
	# Manager/Diwan Officer/Department Head/Senior Management, all read=1,
	# no department scoping in this doctype) already say who may see these;
	# nothing custom to add here, just a portal-friendly listing + a link
	# into Frappe's own /printview for the existing Delivery Sheet Print
	# format rather than re-rendering it ourselves.
	context.sheets = frappe.get_list(
		"Delivery Sheet",
		fields=["name", "delivery_method", "recipient_party", "status", "modified"],
		order_by="modified desc",
		limit_page_length=100,
	)
	return context
