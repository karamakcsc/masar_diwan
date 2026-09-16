"""Department + confidentiality access control for Correspondence.

Standard Frappe role permissions (Role Permission Manager / DocType
`permissions`) only say which roles may touch the Correspondence doctype at
all. The actual per-document decision - "can THIS user see THIS
correspondence" - is entirely driven by two independent, stacked rules:

1. Department scoping: a user may only see correspondence belonging to a
   department they are explicitly linked to (via `User Permission` on
   Department), unless their role is exempt (Diwan Officer, Senior
   Management always see across departments, subject to rule 2 below).
   The `department` field on Correspondence has `ignore_user_permissions=1`
   so Frappe's own automatic Link-field User Permission enforcement never
   doubles up with (or silently overrides) the logic below.

2. Confidentiality tiering, evaluated independently of department:
   - Normal: department rule only.
   - Confidential: current_owner, department members, authorized_viewers,
     Diwan Officer, Senior Management.
   - Highly Confidential: only authorized_viewers + Senior Management
     (even the assigned Department Head is excluded unless explicitly
     added to authorized_viewers).

Both `has_permission` (single document read/write/etc gate) and
`get_permission_query_conditions` (List/Report View filtering) must agree,
so the list never shows a row the form would then refuse to open.
"""

import frappe

from masar_diwan.access_log import log_event

DEPARTMENT_EXEMPT_ROLES = {"Diwan Officer", "Senior Management"}
CONFIDENTIAL_BYPASS_ROLES = {"Diwan Officer", "Senior Management"}
HIGHLY_CONFIDENTIAL_BYPASS_ROLES = {"Senior Management"}


def get_user_departments(user: str) -> set[str]:
	return set(
		frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Department"},
			pluck="for_value",
		)
	)


def _is_authorized_viewer(reference_name: str, user: str) -> bool:
	return bool(
		frappe.db.exists(
			"Correspondence Authorized Viewer",
			{"parent": reference_name, "parenttype": "Correspondence", "user": user},
		)
	)


def _log_denial(doctype: str, name: str, user: str, reason: str):
	log_event(
		"View",
		result="Denied",
		reason=reason,
		reference_doctype=doctype,
		reference_name=name,
		user=user,
	)


def has_permission(doc, ptype="read", user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True

	roles = set(frappe.get_roles(user))

	if ptype == "create":
		# Confidentiality tiers protect who may *read* an existing document -
		# they don't apply to the act of creating/registering a new one (the
		# creator necessarily already knows the content; there is nothing to
		# leak). Only department scoping applies here, same as the Normal
		# tier below. Without this, e.g. a Diwan Officer directly creating a
		# Highly Confidential Correspondence outside the diwan-tray approval
		# path (which uses ignore_permissions=True) would be wrongly denied,
		# since they aren't in HIGHLY_CONFIDENTIAL_BYPASS_ROLES for *reading*.
		if roles & DEPARTMENT_EXEMPT_ROLES:
			return True
		if not doc.department:
			return True
		if doc.department in get_user_departments(user):
			return True
		_log_denial(doc.doctype, doc.name or "(new)", user, "Create: outside user's department")
		return False

	if doc.confidentiality == "Highly Confidential":
		if roles & HIGHLY_CONFIDENTIAL_BYPASS_ROLES:
			return True
		if _is_authorized_viewer(doc.name, user):
			return True
		_log_denial(doc.doctype, doc.name, user, "Highly Confidential: not an authorized viewer")
		return False

	if doc.confidentiality == "Confidential":
		if roles & CONFIDENTIAL_BYPASS_ROLES:
			return True
		if doc.current_owner == user:
			return True
		if _is_authorized_viewer(doc.name, user):
			return True
		if doc.department and doc.department in get_user_departments(user):
			return True
		_log_denial(doc.doctype, doc.name, user, "Confidential: not owner/department/authorized")
		return False

	# Normal
	if roles & DEPARTMENT_EXEMPT_ROLES:
		return True
	if not doc.department:
		return True
	if doc.department in get_user_departments(user):
		return True
	_log_denial(doc.doctype, doc.name, user, "Normal: outside user's department")
	return False


def get_permission_query_conditions(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return ""

	roles = set(frappe.get_roles(user))
	departments = get_user_departments(user)
	escaped_user = frappe.db.escape(user)

	if roles & HIGHLY_CONFIDENTIAL_BYPASS_ROLES:
		# Senior Management: unrestricted.
		return ""

	authorized_viewer_exists = (
		"exists (select 1 from `tabCorrespondence Authorized Viewer` cav "
		"where cav.parenttype = 'Correspondence' and cav.parent = `tabCorrespondence`.name "
		f"and cav.user = {escaped_user})"
	)

	highly_confidential_clause = f"(confidentiality != 'Highly Confidential' or {authorized_viewer_exists})"

	if roles & CONFIDENTIAL_BYPASS_ROLES:
		# Diwan Officer: sees Normal + Confidential everywhere, Highly Confidential only if authorized.
		return highly_confidential_clause

	department_list = ", ".join(frappe.db.escape(d) for d in departments) if departments else ""
	department_clause = (
		f"(department is null or department in ({department_list}))"
		if department_list
		else "department is null"
	)

	confidential_clause = (
		"(confidentiality != 'Confidential' or "
		f"current_owner = {escaped_user} or {authorized_viewer_exists} or {department_clause})"
	)

	return f"({department_clause}) and {confidential_clause} and {highly_confidential_clause}"
