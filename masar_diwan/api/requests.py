"""Read-only helper backing the "New Correspondence Request" Desk Page.

Only exposes what the page's informational banner needs to display before a
`Correspondence Request` exists yet (full name / department / today's date).
The actual document creation and Draft -> Pending Review transition are done
directly from the page's JS via the standard `frappe.client.insert` and
`frappe.model.workflow.apply_workflow` whitelisted methods, reusing
`CorrespondenceRequest.before_insert()` and the existing
`Correspondence Request Workflow` as-is - nothing here duplicates that logic.
"""

import frappe

from masar_diwan.permissions import get_user_departments
from masar_diwan.utils.dynamic_fields import get_active_dynamic_field_rows

DYNAMIC_FIELD_ROW_FIELDS = ["label", "fieldname_slug", "fieldtype", "options", "reqd", "sort_order"]


@frappe.whitelist()
def get_submitter_context():
	user = frappe.session.user
	departments = get_user_departments(user)
	return {
		"full_name": frappe.utils.get_fullname(user),
		"department": next(iter(departments), None),
		"date": frappe.utils.today(),
	}


@frappe.whitelist(allow_guest=False)
def get_confidentiality_levels():
	"""Public, read-only list of the site's Confidentiality Level records,
	ordered least -> most restrictive.

	Confidentiality Level itself only grants DocPerm read to System Manager /
	Diwan Officer / Senior Management (see its DocType JSON) - but every
	submitter-facing picker (the "New Correspondence Request" Desk Page, and
	the Requester Portal's /diwan/submit, reachable by a plain Website User)
	needs to render whichever levels this site is actually configured with,
	not a hardcoded three. This intentionally exposes only the display-safe
	fields (name/label/rank) with ignore_permissions=True - never
	bypass_roles or department_members_can_read/owner_can_read, which are
	access-control configuration, not something a submitter needs to see.
	Real enforcement of who may later read a document at a given level is
	still done entirely by permissions.py; this endpoint only lets the UI
	stop hardcoding level names/colors that the backend has been able to
	vary per client since the Document Access Profile rewrite.
	"""
	return frappe.get_all(
		"Confidentiality Level",
		fields=["name", "level_name", "level_name_en", "rank"],
		order_by="rank asc",
		ignore_permissions=True,
	)


@frappe.whitelist(allow_guest=False)
def get_top_level_categories():
	"""Both hand-built request-creation surfaces (the Desk "New Request" page
	and /diwan/submit's portal form) need to render the same category/
	sub-category pickers the standard Desk form's link_filters already give
	it for free - this and the two functions below are that one shared
	source, called from both instead of each re-querying Correspondence
	Category on its own.
	"""
	return frappe.get_all(
		"Correspondence Category",
		filters=[["disabled", "=", 0], ["parent_correspondence_category", "is", "not set"]],
		fields=["name", "title", "is_group"],
		order_by="title asc",
		ignore_permissions=True,
	)


@frappe.whitelist(allow_guest=False)
def get_sub_categories(correspondence_category: str):
	return frappe.get_all(
		"Correspondence Category",
		filters=[
			["disabled", "=", 0],
			["is_group", "=", 0],
			["parent_correspondence_category", "=", correspondence_category],
		],
		fields=["name", "title"],
		order_by="title asc",
		ignore_permissions=True,
	)


@frappe.whitelist(allow_guest=False)
def get_dynamic_fields(correspondence_category: str | None = None, correspondence_sub_category: str | None = None):
	"""Active dynamic-field definitions for whichever category is actually
	selected - the sub-category if one was chosen, else the top-level
	category itself when it has no children (see
	CorrespondenceRequest._copy_dynamic_field_values() for why this is the
	same "effective category" rule used at Approve & Register time).
	"""
	effective_category = correspondence_sub_category or correspondence_category
	rows = get_active_dynamic_field_rows(effective_category)
	return [{k: row.get(k) for k in DYNAMIC_FIELD_ROW_FIELDS} for row in rows]
