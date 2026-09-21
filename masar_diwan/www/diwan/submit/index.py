import frappe

from masar_diwan.api.requests import get_submitter_context
from masar_diwan.utils.portal_nav import REQUESTER_PORTAL_NAV as PORTAL_NAV


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/diwan/submit"
		raise frappe.Redirect

	if not frappe.has_permission("Correspondence Request", "create"):
		frappe.throw(
			frappe._("You are not permitted to submit correspondence requests."),
			frappe.PermissionError,
		)

	context.no_cache = 1
	context.title = frappe._("New Correspondence Request")
	context.lang = frappe.local.lang
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = PORTAL_NAV
	context.portal_section_title = "Requester Portal"
	context.active_route = "/diwan/submit"
	context.submitter = get_submitter_context()
	return context
