import frappe

from masar_diwan.access_log import log_event
from masar_diwan.utils.dynamic_fields import get_dynamic_field_values_for_display
from masar_diwan.utils.portal_nav import REQUESTER_PORTAL_NAV as PORTAL_NAV

LIST_FIELDS = [
	"name",
	"request_type",
	"subject",
	"status",
	"request_date",
	"modified",
	"resulting_correspondence",
]

DETAIL_FIELDS = LIST_FIELDS + [
	"party_or_department",
	"draft_text",
	"suggested_priority",
	"suggested_confidentiality",
	"note_to_registrar",
	"decision_note",
	"owner",
]


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/diwan/requests"
		raise frappe.Redirect

	context.no_cache = 1
	context.lang = frappe.local.lang
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = PORTAL_NAV
	context.portal_section_title = "Requester Portal"
	context.active_route = "/diwan/requests"

	name = frappe.form_dict.get("name")
	context.detail = None

	if name:
		context.title = frappe._("Request {0}").format(name)
		# frappe.get_doc + has_permission (not ignore_permissions) so a
		# request belonging to someone else 404s exactly like any other
		# doctype - no separate access check needs writing here.
		if not frappe.db.exists("Correspondence Request", name):
			context.detail = {"not_found": True}
		elif not frappe.has_permission("Correspondence Request", "read", doc=name):
			context.detail = {"not_found": True}
		else:
			doc = frappe.get_doc("Correspondence Request", name)
			context.detail = {f: doc.get(f) for f in DETAIL_FIELDS}
			context.detail["not_found"] = False
			context.detail["category"] = doc.correspondence_category
			context.detail["sub_category"] = doc.correspondence_sub_category
			context.dynamic_field_values = get_dynamic_field_values_for_display(doc)
			if doc.resulting_correspondence:
				ref_no, qr_code = frappe.db.get_value(
					"Correspondence", doc.resulting_correspondence, ["reference_no", "qr_code"]
				)
				context.detail["reference_no"] = ref_no
				context.detail["qr_code"] = qr_code
			context.attachments = frappe.get_all(
				"File",
				filters={"attached_to_doctype": "Correspondence Request", "attached_to_name": name},
				fields=["name", "file_name"],
			)
			# Matches queue/index.py's own detail branch, which already logs a
			# "View" event here - a requester opening their own request detail
			# is just as much a view worth auditing as a Diwan Officer opening
			# it from the queue; this page had been silently skipping it.
			log_event(
				"View",
				reference_doctype="Correspondence Request",
				reference_name=name,
				reason="Requester Portal view",
			)
		context.detail_json = frappe.as_json(context.detail)
	else:
		context.title = frappe._("My Requests")
		# Explicit owner filter, not just permission-query scoping: a
		# DEPARTMENT_EXEMPT_ROLES user (Diwan Officer/Senior Management) has
		# unrestricted read on this doctype for the *Diwan Portal* queue, but
		# "My Requests" must always mean literally their own regardless of
		# what else their role can see - that queue is a separate page.
		context.requests = frappe.get_list(
			"Correspondence Request",
			filters={"owner": frappe.session.user},
			fields=LIST_FIELDS,
			order_by="modified desc",
			limit_page_length=100,
		)

	return context
