import frappe

from masar_diwan.permissions import require_diwan_staff
from masar_diwan.utils.pickers import correspondence_type_options
from masar_diwan.utils.portal_nav import DIWAN_PORTAL_NAV


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/diwan/tray"
		raise frappe.Redirect

	require_diwan_staff()

	context.no_cache = 1
	context.title = frappe._("Bulk Approve")
	context.lang = frappe.local.lang
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = DIWAN_PORTAL_NAV
	context.portal_section_title = "Diwan Portal"
	context.active_route = "/diwan/tray"

	# Only Pending Review, not Under Review - bulk-approving something no one
	# has actually opened and read yet is the tray's whole point (fast-track
	# straightforward, already-clear requests); anything already pulled into
	# individual review belongs on the Queue page instead.
	context.requests = frappe.get_list(
		"Correspondence Request",
		filters={"status": "Pending Review"},
		fields=[
			"name",
			"request_type",
			"subject",
			"requested_by",
			"department",
			"suggested_confidentiality",
			"suggested_priority",
			"request_date",
		],
		order_by="request_date asc",
		limit_page_length=200,
	)
	context.correspondence_types = correspondence_type_options()
	return context
