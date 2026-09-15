import frappe


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/track"
		raise frappe.Redirect

	context.no_cache = 1
	context.title = "Correspondence Tracking"
	context.user = frappe.session.user
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.is_portal_user = (
		frappe.db.get_value("User", frappe.session.user, "user_type") == "Website User"
	)
	context.ref = frappe.form_dict.get("ref")
	context.correspondence_types = frappe.get_all("Correspondence Type", fields=["name", "title"])
	context.statuses = ["Draft", "Under Review", "Referred / In Progress", "Completed", "Archived"]
	return context
