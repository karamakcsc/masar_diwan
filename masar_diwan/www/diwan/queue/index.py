import frappe

from masar_diwan.access_log import log_event
from masar_diwan.permissions import require_diwan_staff
from masar_diwan.utils.dynamic_fields import get_dynamic_field_values_for_display
from masar_diwan.utils.pickers import correspondence_type_options
from masar_diwan.utils.portal_nav import DIWAN_PORTAL_NAV

QUEUE_STATUSES = ["Pending Review", "Under Review", "Approved"]

LIST_FIELDS = [
	"name",
	"request_type",
	"subject",
	"status",
	"request_date",
	"requested_by",
	"requesting_department",
	"suggested_confidentiality",
]

DETAIL_FIELDS = LIST_FIELDS + [
	"correspondence_category",
	"correspondence_sub_category",
	"party_or_department",
	"draft_text",
	"suggested_priority",
	"note_to_registrar",
	"decision_note",
	"correspondence_type",
	"resulting_correspondence",
]


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/diwan/queue"
		raise frappe.Redirect

	require_diwan_staff()

	context.no_cache = 1
	context.lang = frappe.local.lang
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = DIWAN_PORTAL_NAV
	context.portal_section_title = "Diwan Portal"
	context.active_route = "/diwan/queue"

	name = frappe.form_dict.get("name")
	context.detail = None

	if name:
		context.title = frappe._("Review Request")
		if not frappe.db.exists("Correspondence Request", name) or not frappe.has_permission(
			"Correspondence Request", "read", doc=name
		):
			context.detail = {"not_found": True}
		else:
			doc = frappe.get_doc("Correspondence Request", name)
			context.detail = {f: doc.get(f) for f in DETAIL_FIELDS}
			context.detail["not_found"] = False
			context.dynamic_field_values = get_dynamic_field_values_for_display(doc)
			if doc.resulting_correspondence:
				context.detail["qr_code"] = frappe.db.get_value(
					"Correspondence", doc.resulting_correspondence, "qr_code"
				)
			context.attachments = frappe.get_all(
				"File",
				filters={"attached_to_doctype": "Correspondence Request", "attached_to_name": name},
				fields=["name", "file_name"],
			)
			log_event(
				"View",
				reference_doctype="Correspondence Request",
				reference_name=name,
				reason="Diwan Portal review",
			)
		context.detail_json = frappe.as_json(context.detail)
		context.correspondence_types = correspondence_type_options()
	else:
		context.title = frappe._("Queue")
		# get_list applies masar_diwan.permissions.get_permission_query_conditions_correspondence_request -
		# department-scoped for anyone outside DEPARTMENT_EXEMPT_ROLES, unrestricted for Diwan
		# Officer/Senior Management, exactly like the Correspondence list itself.
		context.requests = frappe.get_list(
			"Correspondence Request",
			filters={"status": ["in", QUEUE_STATUSES]},
			fields=LIST_FIELDS,
			order_by="request_date asc",
			limit_page_length=200,
		)

	return context
