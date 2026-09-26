import frappe

from masar_diwan.utils.portal_pagination import get_page
from masar_diwan.access_log import log_event
from masar_diwan.permissions import require_diwan_staff
from masar_diwan.utils.dynamic_fields import get_dynamic_field_values_for_display
from masar_diwan.utils.pickers import correspondence_type_options
from masar_diwan.utils.portal_nav import DIWAN_PORTAL_NAV

QUEUE_STATUSES = ["Pending Review", "Under Review", "Approved"]

TABS = ("queue", "tray", "delivery_sheets", "envelopes", "audit_log")
TAB_LABELS = {
	"queue": "Incoming Requests",
	"tray": "Bulk Approve",
	"delivery_sheets": "Delivery Sheets",
	"envelopes": "Envelopes",
	"audit_log": "Access Log",
}
AUDIT_FILTERABLE = ["event_type", "result", "channel", "reference_doctype"]

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
	"""Diwan Staff Portal - merged 2026-09-26 (was 5 separate pages/routes:
	/diwan/queue, /diwan/tray, /diwan/delivery_sheets, /diwan/envelopes,
	/diwan/audit_log). One URL, ?tab=<one of TABS> (queue is the default and
	stays the primary route, since it's the page staff actually work from
	day to day) - the existing side-nav/rail already just needed its 5 links
	repointed at this one page's 5 tab values (see portal_nav.py) rather than
	5 separate page files. Each tab still only fetches its own data (nothing
	changed about what queries run, just which single route triggers them),
	matching how a staff member only ever looks at one of these at a time
	anyway - not an argument for loading all 5 sections' data on every visit.
	"""
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/diwan/queue"
		raise frappe.Redirect

	require_diwan_staff()

	context.no_cache = 1
	context.lang = frappe.local.lang
	context.user_fullname = frappe.utils.get_fullname(frappe.session.user)
	context.portal_nav = DIWAN_PORTAL_NAV
	context.portal_section_title = "Diwan Portal"

	name = frappe.form_dict.get("name")
	tab = frappe.form_dict.get("tab") or "queue"
	if tab not in TABS:
		tab = "queue"
	if name:
		# A request detail is always the Queue tab's own drill-down - a name
		# in the URL always wins over an unrelated ?tab= value.
		tab = "queue"
	context.active_tab = tab
	context.active_route = "/diwan/queue" if tab == "queue" else f"/diwan/queue?tab={tab}"
	context.tab_label = frappe._(TAB_LABELS[tab])
	context.detail = None

	# Cheap, shared by both tabs that offer a Correspondence Type picker
	# (Queue's own Register step, Tray's batch dropdown) - computing it
	# unconditionally is simpler than duplicating the same call per tab.
	context.correspondence_types = correspondence_type_options()

	if tab == "queue":
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
		else:
			context.title = context.tab_label
			# get_list applies masar_diwan.permissions.get_permission_query_conditions_correspondence_request -
			# department-scoped for anyone outside DEPARTMENT_EXEMPT_ROLES, unrestricted for Diwan
			# Officer/Senior Management, exactly like the Correspondence list itself.
			context.requests = get_page(context,
				"Correspondence Request",
				filters={"status": ["in", QUEUE_STATUSES]},
				fields=LIST_FIELDS,
				order_by="request_date asc",
			)

	elif tab == "tray":
		context.title = context.tab_label
		# Only Pending Review, not Under Review - bulk-approving something no
		# one has actually opened and read yet is the tray's whole point
		# (fast-track straightforward, already-clear requests); anything
		# already pulled into individual review belongs on the Queue tab
		# instead.
		context.tray_requests = get_page(context,
			"Correspondence Request",
			filters={"status": "Pending Review"},
			fields=[
				"name",
				"request_type",
				"subject",
				"requested_by",
				"requesting_department",
				"suggested_confidentiality",
				"suggested_priority",
				"request_date",
			],
			order_by="request_date asc",
		)

	elif tab == "delivery_sheets":
		context.title = context.tab_label
		# Standard frappe.get_list - Delivery Sheet's own DocPerm rows (System
		# Manager/Diwan Officer/Department Head/Senior Management, all read=1,
		# no department scoping in this doctype) already say who may see
		# these; nothing custom to add here, just a portal-friendly listing +
		# a link into Frappe's own /printview for the existing Delivery Sheet
		# Print format rather than re-rendering it ourselves.
		context.sheets = get_page(context,
			"Delivery Sheet",
			fields=["name", "delivery_method", "recipient_party", "status", "modified"],
			order_by="modified desc",
		)

	elif tab == "envelopes":
		context.title = context.tab_label
		context.envelopes = get_page(context,
			"Envelope",
			fields=["name", "status", "creation_date", "linked_delivery_sheet"],
			order_by="modified desc",
		)

	elif tab == "audit_log":
		context.title = context.tab_label
		filters = {}
		for key in AUDIT_FILTERABLE:
			value = frappe.form_dict.get(key)
			if value:
				filters[key] = value
		context.active_filters = filters
		# Doctype-level read/report DocPerm (Diwan Officer/Senior Management/
		# System Manager only, per the doctype's own permissions - see
		# access_log_entry.json) already gates this; nothing custom needed
		# here, same as the existing Desk "Access Log Report" this is a
		# portal equivalent of.
		context.entries = get_page(context,
			"Access Log Entry",
			filters=filters,
			fields=[
				"name",
				"user",
				"event_datetime",
				"event_type",
				"channel",
				"result",
				"reason",
				"reference_doctype",
				"reference_name",
				"ip_address",
				"is_new_ip",
			],
			order_by="event_datetime desc",
		)

	return context
