import frappe

from masar_diwan.utils.portal_i18n import get_portal_messages

from masar_diwan.api.portal import get_tracking_detail

PORTAL_NAV = [
	{"route": "/track", "label": "Track", "icon": "qr"},
]


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/track"
		raise frappe.Redirect

	context.no_cache = 1
	context.title = frappe._("Track Correspondence")
	context.lang = frappe.local.lang
	context.diwan_messages = get_portal_messages()
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = PORTAL_NAV
	context.portal_section_title = "Track"
	context.active_route = "/track"

	ref = frappe.form_dict.get("ref")
	context.ref = ref
	context.result = None

	if ref:
		# Same server-side lookup used by the Desk "Correspondence Tracking"
		# page - single source of truth for the found/restricted/not-found
		# decision, so this page can never diverge from what Desk sees.
		via = frappe.form_dict.get("via") or "qr"
		context.result = get_tracking_detail(ref, via)

	return context
