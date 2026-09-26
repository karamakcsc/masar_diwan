import frappe


def get_context(context):
	"""Merged into /diwan/requests (2026-09-26) - kept as a redirect so any
	existing bookmark/link to this URL still works, instead of 404ing."""
	frappe.local.flags.redirect_location = "/diwan/requests?tab=submit"
	raise frappe.Redirect
