"""Whitelisted endpoints backing correspondence search/tracking.

Called from two front doors that share this one implementation instead of
duplicating it: the `/track` website page for Website Users, and the
"Correspondence Tracking" Desk Page for System Users who'd rather not leave
`/app`. `log_event()`'s own channel inference (Website User -> Portal, else
Desk) is what tells the two callers apart in the Access Log - this module
never hardcodes a channel.

Both the search list and the single-reference lookup reuse
`masar_diwan.permissions` for the actual access decision instead of
re-implementing it, so Desk and Portal never disagree about who can see
what. Department scoping is still a hard filter (rows outside the user's
department simply aren't returned); confidentiality is a soft mask (the row
stays, but subject/party are replaced with a placeholder) per spec 6.4.
"""

import frappe
from frappe import _

from masar_diwan.access_log import log_event
from masar_diwan.permissions import (
	CONFIDENTIAL_BYPASS_ROLES,
	DEPARTMENT_EXEMPT_ROLES,
	get_user_departments,
	has_permission,
)

MASK = "•• مقيّد ••"
RESULT_FIELDS = [
	"name",
	"reference_no",
	"correspondence_type",
	"subject",
	"subject_en",
	"party",
	"status",
	"priority",
	"department",
	"confidentiality",
	"current_owner",
	"document_date",
	"modified",
]


def _mask_if_restricted(row, user):
	stub = frappe._dict(
		doctype="Correspondence",
		name=row["name"],
		confidentiality=row["confidentiality"],
		current_owner=row["current_owner"],
		department=row["department"],
	)
	if has_permission(stub, "read", user):
		return row

	row["subject"] = MASK
	row["subject_en"] = MASK if row.get("subject_en") else None
	row["party"] = MASK
	return row


@frappe.whitelist()
def search_correspondence(
	correspondence_type=None,
	status=None,
	department=None,
	priority=None,
	from_date=None,
	to_date=None,
	text=None,
):
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please log in"), frappe.PermissionError)

	roles = set(frappe.get_roles(user))
	conditions = []
	values = {}

	if not (roles & DEPARTMENT_EXEMPT_ROLES):
		departments = get_user_departments(user)
		if departments:
			placeholders = ", ".join(frappe.db.escape(d) for d in departments)
			conditions.append(f"(department is null or department in ({placeholders}))")
		else:
			conditions.append("department is null")

	if correspondence_type:
		conditions.append("correspondence_type = %(correspondence_type)s")
		values["correspondence_type"] = correspondence_type
	if status:
		conditions.append("status = %(status)s")
		values["status"] = status
	if department:
		conditions.append("department = %(department)s")
		values["department"] = department
	if priority:
		conditions.append("priority = %(priority)s")
		values["priority"] = priority
	if from_date:
		conditions.append("document_date >= %(from_date)s")
		values["from_date"] = from_date
	if to_date:
		conditions.append("document_date <= %(to_date)s")
		values["to_date"] = to_date
	if text:
		conditions.append("(reference_no like %(text)s or subject like %(text)s)")
		values["text"] = f"%{text}%"

	where_clause = f"where {' and '.join(conditions)}" if conditions else ""
	fields = ", ".join(RESULT_FIELDS)

	rows = frappe.db.sql(
		f"select {fields} from `tabCorrespondence` {where_clause} order by modified desc limit 100",
		values,
		as_dict=True,
	)

	log_event("View", reason="Correspondence search")

	return [_mask_if_restricted(r, user) for r in rows]


@frappe.whitelist(allow_guest=True)
def get_tracking_detail(ref: str, via: str = "qr"):
	user = frappe.session.user
	if user == "Guest":
		frappe.throw(_("Please log in to view tracking details"), frappe.PermissionError)

	event_type = "Barcode Scan" if via == "barcode" else "QR Scan"

	if not frappe.db.exists("Correspondence", ref):
		log_event(
			event_type,
			result="Denied",
			reason="Reference not found",
			reference_doctype="Correspondence",
			reference_name=ref,
		)
		return {"found": False}

	doc = frappe.get_doc("Correspondence", ref)
	allowed = has_permission(doc, "read", user)

	log_event(
		event_type,
		result="Success" if allowed else "Denied",
		reason=None if allowed else "No read permission",
		reference_doctype="Correspondence",
		reference_name=ref,
	)

	if not allowed:
		return {"found": True, "restricted": True}

	attachments = frappe.get_all(
		"File",
		filters={"attached_to_doctype": "Correspondence", "attached_to_name": ref},
		fields=["name", "file_name", "file_url"],
	)

	return {
		"found": True,
		"restricted": False,
		"data": {f: doc.get(f) for f in RESULT_FIELDS},
		"attachments": attachments,
	}


@frappe.whitelist()
def download_attachment(file_id: str):
	"""Logged replacement for the raw /private/files/... route (Phase 6's
	own TODO): re-checks permission on the *Correspondence* the file is
	attached to (not just the File doctype itself), logs a Download event
	either way, and only then streams the content.
	"""
	if not frappe.db.exists("File", file_id):
		frappe.throw(_("File not found"), frappe.DoesNotExistError)

	file_doc = frappe.get_doc("File", file_id)
	user = frappe.session.user

	if file_doc.attached_to_doctype != "Correspondence" or not file_doc.attached_to_name:
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	reference_name = file_doc.attached_to_name
	allowed = frappe.db.exists("Correspondence", reference_name) and has_permission(
		frappe.get_doc("Correspondence", reference_name), "read", user
	)

	log_event(
		"Download",
		result="Success" if allowed else "Denied",
		reason=None if allowed else "No read permission on the attached Correspondence",
		reference_doctype="Correspondence",
		reference_name=reference_name,
		file_name=file_doc.file_name,
	)

	if not allowed:
		frappe.throw(_("You are not permitted to download this file"), frappe.PermissionError)

	frappe.local.response.filename = file_doc.file_name
	frappe.local.response.filecontent = file_doc.get_content()
	frappe.local.response.type = "download"
