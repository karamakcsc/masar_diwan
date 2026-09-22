import frappe

from masar_diwan.api.requests import get_confidentiality_levels, get_submitter_context
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
	# Rendered server-side (like the rest of this page) rather than fetched
	# by the page's own JS - the list is site-configurable (see Document
	# Access Profile / Confidentiality Level), not a fixed set of 3, so the
	# radio pillgroup below is built from whatever this call returns instead
	# of 3 hardcoded options.
	context.confidentiality_levels = get_confidentiality_levels()
	return context
