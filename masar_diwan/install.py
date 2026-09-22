import json
import os

import frappe

ROLES = [
	"Correspondence Employee",
	"Department Head",
	"Diwan Officer",
	"Senior Management",
	"Portal Tracking User",
]

LEGACY_DEPARTMENT_DOCTYPE = "Masar Diwan Legacy Department"

# (doctype, fieldname) pairs that Link to "Department" - whichever doctype
# is currently providing it (ERPNext's real one, or ours, see
# ensure_department_doctype() below).
DEPARTMENT_LINK_FIELDS = [
	("Correspondence", "department"),
	("Correspondence Request", "department"),
	("Correspondence Transfer Log", "to_department"),
]


def after_install():
	create_roles()
	ensure_workspace_sidebar()
	ensure_desktop_icon()
	ensure_department_doctype()


def before_migrate():
	try:
		rename_masar_department_before_erpnext_sync()
	except Exception:
		frappe.log_error(title="masar_diwan: before_migrate department rename failed")


def after_migrate():
	ensure_workspace_sidebar()
	ensure_desktop_icon()
	ensure_department_doctype()
	try:
		migrate_legacy_department_to_erpnext()
	except Exception:
		frappe.log_error(title="masar_diwan: after_migrate department migration failed")


def create_roles():
	for role_name in ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.new_doc("Role")
		role.role_name = role_name
		role.desk_access = 0 if role_name == "Portal Tracking User" else 1
		role.insert(ignore_permissions=True)


def ensure_workspace_sidebar():
	"""A public Workspace only shows up in the Desk home grid if it also has
	a matching `Workspace Sidebar` row (a separate doctype from `Workspace`
	itself, populated by `frappe.boot.workspace_sidebar_item`). Frappe only
	auto-creates that row once, via `auto_generate_icons_and_sidebar()` during
	`bench install-app` - if a public Workspace gets created or renamed
	*after* that point (which is exactly what happened here: "Masar Diwan"
	was built and inserted programmatically well after this app's own
	install-app run), it never gets a sidebar entry and silently never
	appears in the grid, even though the Workspace record itself is
	perfectly valid (public=1, is_hidden=0) and `get_workspaces()` still
	lists it correctly - that API isn't what renders the home grid.
	Re-running Frappe's own official, idempotent generator on every migrate
	(not just after_install) makes this self-healing for any future
	Workspace this app adds or changes.
	"""
	try:
		from frappe.desk.doctype.workspace_sidebar.workspace_sidebar import (
			create_workspace_sidebar_for_workspaces,
		)

		create_workspace_sidebar_for_workspaces()
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="masar_diwan: failed to ensure Workspace Sidebar")


def ensure_desktop_icon():
	"""The Desk home grid (the actual "app switcher" grid of tiles - Framework,
	Organization, Accounting, Buying, Stock, ...) is driven by a *third*,
	still different doctype: `Desktop Icon`. Neither `Workspace` (public=1,
	is_hidden=0) nor `Workspace Sidebar` (fixed above) puts a tile on this
	specific grid - only a `Desktop Icon` row does. Same story as
	`ensure_workspace_sidebar()`: Frappe only auto-creates these once, via
	`create_desktop_icons()` during `bench install-app`, which ran before
	the "Masar Diwan" Workspace existed. `create_desktop_icons_from_workspace()`
	is Frappe's own official, idempotent generator for exactly this (guarded
	by `if not frappe.db.exists("Desktop Icon", label)`), so re-running it on
	every migrate is safe and makes this self-healing too.
	"""
	try:
		from frappe.desk.doctype.desktop_icon.desktop_icon import create_desktop_icons

		create_desktop_icons()
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="masar_diwan: failed to ensure Desktop Icon")


def ensure_department_doctype():
	"""`Department` (the doctype `Correspondence.department`,
	`Correspondence Request.department`, and
	`Correspondence Transfer Log.to_department` all Link to, and the one
	`get_user_departments()`/the whole department-scoping layer of the
	permission engine is built around) is itself an **ERPNext** doctype
	(`erpnext/setup/doctype/department`) - not core Frappe, and not part of
	`hrms` either. On a genuinely Frappe-only site it doesn't exist at all:
	no `DocType` record, no table, and even attempting to create one throws
	`ImportError` (confirmed directly against a real Frappe-only test site,
	2026-09-22).

	Provide masar_diwan's own "Department" - same literal name, so the three
	Link fields above never need editing either way - as a `custom=1`
	DocType (no physical controller file needed or wanted; `custom=1`
	doctypes use the generic `frappe.model.document.Document` class per
	`frappe.model.base_document.import_controller()`), but only when
	ERPNext genuinely isn't installed and nothing named "Department"
	already exists. The moment ERPNext gets installed later,
	`rename_masar_department_before_erpnext_sync()`/
	`migrate_legacy_department_to_erpnext()` below hand off to ERPNext's
	real one automatically - this function only ever provides a fallback,
	never competes with the real thing.
	"""
	try:
		if "erpnext" in frappe.get_installed_apps():
			return
		if frappe.db.exists("DocType", "Department"):
			return
		_create_masar_department_doctype()
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="masar_diwan: failed to ensure Department doctype")


def _create_masar_department_doctype():
	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": "Department",
			"module": "Masar Diwan",
			"custom": 1,
			"autoname": "field:department_name",
			"naming_rule": "By fieldname",
			"fields": [
				{
					"fieldname": "department_name",
					"label": "Department Name",
					"fieldtype": "Data",
					"reqd": 1,
					"unique": 1,
					"in_list_view": 1,
				},
				{
					# No `company`/accounting concept at all, deliberately - this
					# fallback exists only for Frappe-only deployments, where
					# "Company" (also ERPNext) doesn't exist either. A plain
					# self-Link, not a full NestedSet tree (`is_tree`) - nothing
					# in this app ever traverses department hierarchy, so the
					# extra lft/rgt bookkeeping a real tree doctype needs isn't
					# earning its complexity here.
					"fieldname": "parent_department",
					"label": "Parent Department",
					"fieldtype": "Link",
					"options": "Department",
				},
			],
			"permissions": [
				{
					"role": "System Manager",
					"read": 1,
					"write": 1,
					"create": 1,
					"delete": 1,
					"email": 1,
					"export": 1,
					"print": 1,
					"report": 1,
					"share": 1,
				},
				{
					"role": "Diwan Officer",
					"read": 1,
					"write": 1,
					"create": 1,
					"email": 1,
					"print": 1,
					"report": 1,
				},
				{"role": "Department Head", "read": 1},
				{"role": "Correspondence Employee", "read": 1},
				{"role": "Senior Management", "read": 1},
			],
			"track_changes": 1,
		}
	)
	doc.insert(ignore_permissions=True)


def rename_masar_department_before_erpnext_sync():
	"""Must run in `before_migrate`, not `after_migrate` - if we waited,
	ERPNext's own migrate would already have synced its real `Department`
	(module "Setup") over/alongside ours within the *same* migrate run,
	producing an unpredictable metadata collision instead of a clean
	rename. Renaming our synthetic doctype out of the way first leaves the
	name free for ERPNext's own sync to claim normally, later in this same
	migrate.

	No-ops immediately, on the very first check, for any site where ERPNext
	already provides the real `Department` (e.g. `bob.local`) - `module`
	will already be "Setup", never "Masar Diwan", so this never touches a
	real ERPNext Department under any circumstance.
	"""
	if "erpnext" not in frappe.get_installed_apps():
		return
	module = frappe.db.get_value("DocType", "Department", "module")
	if module != "Masar Diwan":
		return

	frappe.rename_doc("DocType", "Department", LEGACY_DEPARTMENT_DOCTYPE, force=True)
	frappe.db.commit()


def migrate_legacy_department_to_erpnext():
	"""Runs every `after_migrate`; a no-op almost always (nothing pending),
	self-healing/idempotent/retry-safe otherwise - matching every other
	hook in this file. See `rename_masar_department_before_erpnext_sync()`
	above for the rename step this follows.
	"""
	if not frappe.db.exists("DocType", LEGACY_DEPARTMENT_DOCTYPE):
		return  # nothing pending

	real_department_module = frappe.db.get_value("DocType", "Department", "module")
	if real_department_module != "Setup":
		# ERPNext is installed (or the legacy doctype wouldn't exist at all -
		# see the rename step) but hasn't synced its own Department yet in
		# this migrate run. Retry on the next one.
		return

	if not frappe.db.count("Company"):
		frappe.log_error(
			title="masar_diwan: Department migration deferred (no Company yet)",
			message=(
				"ERPNext is installed and its real Department doctype exists, but no "
				"Company record exists yet (Setup Wizard likely hasn't run). Deferring "
				"the legacy department migration until at least one Company exists - "
				"will retry automatically on every future migrate."
			),
		)
		return

	legacy_rows = frappe.get_all(LEGACY_DEPARTMENT_DOCTYPE, fields=["name", "department_name"])
	if legacy_rows:
		_backup_legacy_departments(legacy_rows)

		for row in legacy_rows:
			match = _find_unambiguous_matching_department(row.department_name)
			if not match:
				frappe.log_error(
					title="masar_diwan: legacy department not migrated (no unambiguous match)",
					message=(
						f"Legacy department {row.name!r} (department_name={row.department_name!r}) "
						"has no unambiguous match among ERPNext's real Department records "
						"(zero, or more than one across different companies). Left as-is - "
						"needs a manual decision, not something to guess automatically."
					),
				)
				continue
			_migrate_department_references(row.name, match)

	_cleanup_fully_migrated_legacy_departments()


def _backup_legacy_departments(rows):
	"""A durable audit trail of every legacy department row that existed
	right before migration started, written before any deletion - so the
	original data/names are recoverable even after the legacy doctype and
	its rows are eventually cleaned up."""
	backup_dir = frappe.get_site_path("private", "backups", "masar_diwan")
	os.makedirs(backup_dir, exist_ok=True)
	timestamp = frappe.utils.now_datetime().strftime("%Y%m%d_%H%M%S")
	path = os.path.join(backup_dir, f"legacy_department_backup_{timestamp}.json")
	with open(path, "w") as f:
		json.dump(rows, f, indent=2, default=str)


def _find_unambiguous_matching_department(department_name):
	"""Match by department_name only, as decided - deliberately not by
	`name` (ERPNext's own autoname convention, typically
	"{department_name} - {company abbr}", has no equivalent on the legacy
	side to compare against)."""
	matches = frappe.get_all("Department", filters={"department_name": department_name}, pluck="name")
	if len(matches) == 1:
		return matches[0]
	return None


def _migrate_department_references(old_name, new_name):
	for doctype, fieldname in DEPARTMENT_LINK_FIELDS:
		frappe.db.set_value(doctype, {fieldname: old_name}, fieldname, new_name)

	frappe.db.sql(
		"""update `tabUser Permission` set for_value = %s
		where allow = 'Department' and for_value = %s""",
		(new_name, old_name),
	)
	frappe.db.commit()


def _any_references_remain(legacy_department_name):
	for doctype, fieldname in DEPARTMENT_LINK_FIELDS:
		if frappe.db.exists(doctype, {fieldname: legacy_department_name}):
			return True
	if frappe.db.exists("User Permission", {"allow": "Department", "for_value": legacy_department_name}):
		return True
	return False


def _cleanup_fully_migrated_legacy_departments():
	"""Deletes only the legacy department rows that have zero remaining
	real references anywhere (fully migrated, or never actually referenced
	in the first place) - an ambiguous/unmigrated row with live references
	is left alone entirely, rows and all, exactly as decided. Only drops
	the whole `Masar Diwan Legacy Department` doctype, and only repoints
	the three real Link fields' `options` back to plain "Department", once
	*every* row is gone - never while any reference could still be
	dangling."""
	remaining = frappe.get_all(LEGACY_DEPARTMENT_DOCTYPE, pluck="name")
	for name in remaining:
		if _any_references_remain(name):
			continue
		frappe.delete_doc(LEGACY_DEPARTMENT_DOCTYPE, name, force=True, ignore_permissions=True)

	frappe.db.commit()

	if frappe.get_all(LEGACY_DEPARTMENT_DOCTYPE, limit=1):
		return  # still at least one blocked row - leave the doctype in place

	frappe.delete_doc("DocType", LEGACY_DEPARTMENT_DOCTYPE, force=True, ignore_permissions=True)
	_restore_department_field_options()
	frappe.db.commit()


def _restore_department_field_options():
	"""Renaming "Department" -> "Masar Diwan Legacy Department" earlier
	(via the standard `frappe.rename_doc`) correctly, automatically
	re-pointed these three fields' `options` at the renamed doctype - and,
	on a `developer_mode` site, also rewrote that value straight into this
	app's own tracked `correspondence.json`/etc. source files on disk as a
	side effect (`update_options_for_fieldtype()`'s dev-mode branch calls
	`.save()` on every affected DocType, which re-exports it). That source
	content must never actually say anything but "Department" long-term -
	fixed properly through the ORM (edit the field, `doc.save()`) rather
	than a raw DB patch or `frappe.reload_doc()`, since only a real `save()`
	both corrects the live DocField row *and* re-exports the JSON file with
	the corrected value - `reload_doc` would just re-import whatever the
	(possibly still wrong) file on disk already says.
	"""
	for doctype, fieldname in DEPARTMENT_LINK_FIELDS:
		dt_doc = frappe.get_doc("DocType", doctype)
		changed = False
		for f in dt_doc.fields:
			if f.fieldname == fieldname and f.options != "Department":
				f.options = "Department"
				changed = True
		if changed:
			dt_doc.save(ignore_permissions=True)
