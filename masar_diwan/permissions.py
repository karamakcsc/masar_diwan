"""Generic department + confidentiality access control engine.

Any doctype registered in the **Document Access Profile** master gets the
same two independent, stacked rules, driven entirely by that master (and, for
confidentiality, the **Confidentiality Level** master) instead of logic
hardcoded around any one doctype:

1. Department scoping: a user may only see a document belonging to a
   department they are explicitly linked to (via `User Permission` on
   Department), unless their role is in that document type's
   `department_exempt_roles`. A profile can list *more than one*
   `department_fields` row (e.g. `from_department` + `to_department` on
   Internal Mail Movement) - a document matches if the user belongs to
   *any one* of them (logical OR). A profile with no department fields at
   all skips this rule entirely for that type; a document where every
   configured department field is empty is likewise treated as
   unrestricted (matches this rule's original single-field behavior
   exactly when there's only one field).

2. Confidentiality tiering (only for profiles with `supports_confidentiality`
   set), evaluated independently of department, via the document's
   `confidentiality_field` value - a Link to **Confidentiality Level**.
   Each level independently configures:
   - `bypass_roles`: roles that read a document at this level from any
     department, regardless of ownership or authorized-viewer status.
   - `owner_can_read`: whether the document's own `owner_field` value
     matching the requesting user grants access outside bypass_roles.
   - `department_members_can_read`: whether plain department membership
     (rule 1) is *also* sufficient at this level, on top of bypass/owner/
     authorized-viewer.
   A document with no confidentiality value set (or a profile that doesn't
   support confidentiality at all) is governed by department scoping alone.

Both `generic_has_permission` (single document read/write/etc gate) and
`generic_get_permission_query_conditions` (List/Report View filtering) must
agree, so the list never shows a row the form would then refuse to open.

`Correspondence`'s own `has_permission`/`get_permission_query_conditions`
(the entry points wired in `hooks.py` - Frappe requires an explicit
registration per doctype, this is the one place that can't be generalized
away) are now thin wrappers over this engine, registered via a
`Document Access Profile` record named "Correspondence". Its exact
configuration (roles, field names, per-level rules) reproduces this app's
original hand-written Correspondence-only logic exactly - see
CLAUDE.md's "generalized permission engine" section for the full mapping
and the verification that behavior didn't change.
"""

import frappe

from masar_diwan.access_log import log_event

# Who the Diwan Portal (queue/tray/print/access log) is for. Deliberately
# narrower than "anyone with desk access to Correspondence Request" - a plain
# Correspondence Employee/Department Head can submit requests but has no
# workflow transition permission past Draft, so the review-side portal isn't
# meant for them. Not part of the generic engine below - this one is
# genuinely Correspondence-Request-specific UI gating, not a per-document
# read/write decision.
DIWAN_STAFF_ROLES = {"Diwan Officer", "Senior Management", "System Manager"}


def require_diwan_staff(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return
	if not (set(frappe.get_roles(user)) & DIWAN_STAFF_ROLES):
		frappe.throw(frappe._("You do not have access to the Diwan Portal."), frappe.PermissionError)


def get_user_departments(user: str) -> set[str]:
	return set(
		frappe.get_all(
			"User Permission",
			filters={"user": user, "allow": "Department"},
			pluck="for_value",
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


def _get_profile(document_type: str):
	"""Cached for the lifetime of the request - Document Access Profile is
	config, not data, and doesn't change mid-request."""
	return frappe.get_cached_doc("Document Access Profile", document_type)


def get_department_exempt_roles(document_type: str) -> set[str]:
	"""Public accessor for callers outside this module that need the same
	role set used internally (e.g. `api/portal.py`'s own raw SQL department
	filter for search results) without duplicating a hardcoded role list."""
	return {r.role for r in _get_profile(document_type).department_exempt_roles}


def _get_confidentiality_level(level_name: str):
	if not level_name:
		return None
	try:
		return frappe.get_cached_doc("Confidentiality Level", level_name)
	except frappe.DoesNotExistError:
		return None


def _get_all_confidentiality_levels():
	names = frappe.get_all("Confidentiality Level", pluck="name", order_by="rank asc")
	return [frappe.get_cached_doc("Confidentiality Level", n) for n in names]


def _is_authorized_viewer(authorized_viewer_doctype: str, parenttype: str, parent: str, user: str) -> bool:
	return bool(
		frappe.db.exists(
			authorized_viewer_doctype,
			{"parent": parent, "parenttype": parenttype, "user": user},
		)
	)


def generic_has_permission(document_type: str, doc, ptype: str = "read", user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True

	profile = _get_profile(document_type)
	roles = set(frappe.get_roles(user))
	dept_exempt_roles = {r.role for r in profile.department_exempt_roles}
	department_fields = [row.fieldname for row in profile.department_fields]

	def department_ok():
		if roles & dept_exempt_roles:
			return True
		if not department_fields:
			return True
		dept_values = [doc.get(fn) for fn in department_fields]
		if not any(dept_values):
			return True
		user_departments = get_user_departments(user)
		return any(v in user_departments for v in dept_values if v)

	if ptype == "create":
		# Confidentiality tiers protect who may *read* an existing document -
		# they don't apply to the act of creating/registering a new one (the
		# creator necessarily already knows the content; there is nothing to
		# leak). Only department scoping applies here.
		if department_ok():
			return True
		_log_denial(doc.doctype, doc.name or "(new)", user, "Create: outside user's department")
		return False

	level = None
	if profile.supports_confidentiality:
		level = _get_confidentiality_level(doc.get(profile.confidentiality_field))

	if level:
		bypass_roles = {r.role for r in level.bypass_roles}
		if roles & bypass_roles:
			return True
		owner_field = profile.owner_field or "owner"
		if level.owner_can_read and doc.get(owner_field) == user:
			return True
		if profile.authorized_viewer_doctype and _is_authorized_viewer(
			profile.authorized_viewer_doctype, doc.doctype, doc.name, user
		):
			return True
		if level.department_members_can_read and department_ok():
			return True
		_log_denial(
			doc.doctype, doc.name, user, f"{level.name}: not owner/department/authorized/bypass"
		)
		return False

	# No confidentiality value set, or the profile doesn't support tiering -
	# plain department scoping.
	if department_ok():
		return True
	_log_denial(doc.doctype, doc.name, user, "Outside user's department")
	return False


def generic_get_permission_query_conditions(document_type: str, user: str | None = None) -> str:
	user = user or frappe.session.user
	if user == "Administrator":
		return ""

	profile = _get_profile(document_type)
	roles = set(frappe.get_roles(user))
	dept_exempt_roles = {r.role for r in profile.department_exempt_roles}
	department_fields = [row.fieldname for row in profile.department_fields]
	escaped_user = frappe.db.escape(user)

	def department_clause():
		"""None means "not restrictive" (no department fields, or user is
		department-exempt) - the caller must treat that as always-true,
		not as an empty/false condition. With multiple department fields,
		a row matches if ANY one of them holds one of the user's
		departments (OR across fields) - or if every one of them is empty
		(unrestricted, same fallback as the single-field case)."""
		if roles & dept_exempt_roles or not department_fields:
			return None
		departments = get_user_departments(user)
		department_list = ", ".join(frappe.db.escape(d) for d in departments) if departments else ""
		all_empty_clause = " and ".join(f"{fn} is null" for fn in department_fields)
		if not department_list:
			return f"({all_empty_clause})"
		field_match_clauses = [f"{fn} in ({department_list})" for fn in department_fields]
		return "(" + " or ".join(field_match_clauses) + f" or ({all_empty_clause}))"

	if not profile.supports_confidentiality:
		clause = department_clause()
		return clause or ""

	conf_field = profile.confidentiality_field
	owner_field = profile.owner_field or "owner"
	levels = _get_all_confidentiality_levels()
	dept_clause = department_clause()

	def authorized_viewer_sql():
		if not profile.authorized_viewer_doctype:
			return None
		return (
			f"exists (select 1 from `tab{profile.authorized_viewer_doctype}` av "
			f"where av.parenttype = {frappe.db.escape(document_type)} and av.parent = `tab{document_type}`.name "
			f"and av.user = {escaped_user})"
		)

	per_level_clauses = []
	for level in levels:
		bypass_roles = {r.role for r in level.bypass_roles}
		escaped_level = frappe.db.escape(level.name)
		if roles & bypass_roles:
			per_level_clauses.append(f"{conf_field} = {escaped_level}")
			continue

		sub_conditions = []
		if level.owner_can_read:
			sub_conditions.append(f"{owner_field} = {escaped_user}")
		av_sql = authorized_viewer_sql()
		if av_sql:
			sub_conditions.append(av_sql)
		if level.department_members_can_read:
			sub_conditions.append(dept_clause if dept_clause is not None else "1=1")

		if sub_conditions:
			per_level_clauses.append(f"({conf_field} = {escaped_level} and ({' or '.join(sub_conditions)}))")
		# else: no path grants access at this level for this user - omit,
		# rows at this level are excluded entirely.

	known_levels_sql = ", ".join(frappe.db.escape(l.name) for l in levels)
	no_tiering_condition = (
		f"({conf_field} is null or {conf_field} not in ({known_levels_sql}))" if known_levels_sql else "1=1"
	)
	no_tiering_clause = (
		f"({no_tiering_condition} and {dept_clause})" if dept_clause is not None else no_tiering_condition
	)

	all_clauses = per_level_clauses + [no_tiering_clause]
	return "(" + " or ".join(all_clauses) + ")"


def has_permission(doc, ptype="read", user=None):
	return generic_has_permission("Correspondence", doc, ptype, user)


def get_permission_query_conditions(user=None):
	return generic_get_permission_query_conditions("Correspondence", user)


def has_permission_internal_mail_movement(doc, ptype="read", user=None):
	return generic_has_permission("Internal Mail Movement", doc, ptype, user)


def get_permission_query_conditions_internal_mail_movement(user=None):
	return generic_get_permission_query_conditions("Internal Mail Movement", user)


# Correspondence Request only. These are the business-process reviewer
# roles whose department-exempt bypass must NOT extend to a request still
# being drafted by its own owner (status == "Draft", not yet Submitted) -
# their involvement is meant to start only once it reaches "Pending Review".
# System Manager is deliberately excluded from this set even though it's
# also in Correspondence's own department_exempt_roles: it's an
# administrative/technical role already exempt from every department and
# confidentiality restriction on the *registered* Correspondence itself
# (including Highly Confidential), so carving out just this one earlier,
# narrower stage for it alone would be an inconsistent, no-real-security-
# benefit restriction, not a meaningful boundary. See CLAUDE.md, 2026-09-25
# "Draft visibility" section, for the full reasoning and the empirical
# proof of the gap this closes.
DRAFT_STAGE_RESTRICTED_ROLES = {"Diwan Officer", "Senior Management"}


def has_permission_correspondence_request(doc, ptype="read", user=None):
	"""Department scoping for Correspondence Request, layered on top of the
	if_owner DocPerm rows (Correspondence Employee/Department Head/Portal
	Tracking User) already in the doctype's own permissions table. Frappe's
	controller has_permission hook can only *narrow* a base DocPerm grant,
	never widen it (see frappe.permissions.has_controller_permissions), so
	this only needs to say when to deny, mirroring the Correspondence model
	in this same module for the Diwan Portal queue to be scoped the same
	way the Correspondence list already is.

	Not yet migrated onto the generic Document Access Profile engine above -
	Correspondence Request has no confidentiality tiering at all, and its own
	department-exempt role set has always been identical to Correspondence's
	by coincidence, not by shared config. Left as its own small function
	rather than forcing a confidentiality-less doctype through the same
	profile shape; a natural follow-up if a future confidentiality-less type
	needs the exact same department-only pattern a third time.
	"""
	user = user or frappe.session.user
	if user == "Administrator":
		return True

	roles = set(frappe.get_roles(user))
	department_exempt_roles = {r.role for r in _get_profile("Correspondence").department_exempt_roles}

	still_drafting = doc.get("status") == "Draft" and doc.owner != user
	blocked_while_drafting = still_drafting and (roles & DRAFT_STAGE_RESTRICTED_ROLES) and not (
		roles - DRAFT_STAGE_RESTRICTED_ROLES
	) & department_exempt_roles

	if (roles & department_exempt_roles) and not blocked_while_drafting:
		return True
	if doc.owner == user:
		return True
	if still_drafting:
		_log_denial(doc.doctype, doc.name or "(new)", user, "Draft not yet submitted")
		return False
	if not doc.requesting_department:
		return True
	if doc.requesting_department in get_user_departments(user):
		return True

	_log_denial(doc.doctype, doc.name or "(new)", user, "Outside user's department")
	return False


def get_permission_query_conditions_correspondence_request(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return ""

	roles = set(frappe.get_roles(user))
	department_exempt_roles = {r.role for r in _get_profile("Correspondence").department_exempt_roles}
	escaped_user = frappe.db.escape(user)

	if roles & department_exempt_roles:
		if (roles & DRAFT_STAGE_RESTRICTED_ROLES) and not (roles - DRAFT_STAGE_RESTRICTED_ROLES) & department_exempt_roles:
			# Unrestricted except for someone else's still-drafting request.
			return f"(status != 'Draft' or owner = {escaped_user})"
		return ""

	departments = get_user_departments(user)
	department_list = ", ".join(frappe.db.escape(d) for d in departments) if departments else ""
	department_clause = (
		f"(requesting_department is null or requesting_department in ({department_list}))"
		if department_list
		else "requesting_department is null"
	)

	return f"(owner = {escaped_user} or {department_clause})"
