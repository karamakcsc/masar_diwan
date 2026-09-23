import json
import os

import frappe
from frappe.modules.import_file import import_file_by_path

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
	("Correspondence Request", "requesting_department"),
	("Correspondence Transfer Log", "to_department"),
]


DEPARTMENT_READ_ROLES = [
	"Correspondence Employee",
	"Department Head",
	"Diwan Officer",
	"Senior Management",
]


def after_install():
	create_roles()
	ensure_workspace_sidebar()
	ensure_desktop_icon()
	ensure_department_doctype()
	ensure_department_read_access()
	ensure_workflows()
	ensure_workflow_states()
	ensure_dynamic_fields()


def before_migrate():
	try:
		rename_masar_department_before_erpnext_sync()
	except Exception:
		frappe.log_error(title="masar_diwan: before_migrate department rename failed")


def after_migrate():
	ensure_workspace_sidebar()
	ensure_desktop_icon()
	ensure_department_doctype()
	ensure_department_read_access()
	ensure_workflows()
	ensure_workflow_states()
	ensure_dynamic_fields()
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


def ensure_workflows():
	"""Found 2026-09-22 while running a real end-to-end test on `diwan.local`
	(a fresh `bench install-app masar_diwan`, no data ever hand-seeded there
	beyond fixtures): every single workflow transition failed, and none of
	this app's 3 `Workflow` records (`Correspondence Workflow`,
	`Correspondence Request Workflow`, `Delivery Sheet Workflow`) existed in
	its database at all - confirmed directly (`select * from tabWorkflow`:
	zero rows), despite `bench migrate` reporting zero errors every time.

	Root cause, confirmed by reading `frappe/model/sync.py` directly: Frappe's
	own `sync_all()`/`sync_for()` only auto-imports a fixed, explicit list of
	content types from an app's module folders (`IMPORTABLE_DOCTYPES`:
	DocType, Page, Report, Print Format, Workspace, Onboarding Step, Client
	Script, Custom Field, Property Setter, and a handful more) - `"workflow"`
	does not appear anywhere in that file. **Frappe never auto-syncs Workflow
	JSON files from an app's `<module>/workflow/*/*.json` into the database
	on install or migrate, for any app** - this is a general Frappe
	limitation, not something specific to this site or this app. This
	project's 3 workflows only ever existed on `bob.local` because they were
	originally created via one-off interactive Python scripts during this
	app's own build (see the "gotcha #6" entry elsewhere in this file's
	CLAUDE.md counterpart) and *exported* to JSON afterward for version
	control - nothing ever closed the loop and made that JSON re-importable
	on a fresh install. Every fresh `bench install-app masar_diwan`, on any
	site, until this fix, would have had a completely non-functional
	correspondence workflow and Diwan Tray - not a data problem, a genuine
	installation gap.

	Fixed using Frappe's own official, generic, reusable importer,
	`frappe.modules.import_file.import_file_by_path()` - the exact function
	`sync_for()` itself calls for every doctype in `IMPORTABLE_DOCTYPES` -
	called directly against each workflow JSON path, which `sync_for()`
	simply never does for `"workflow"`. It's naturally idempotent (compares
	a stored hash/modified-timestamp before doing anything, per its own
	docstring), so calling it on every migrate is safe and self-healing,
	matching every other hook in this file.
	"""
	try:
		workflow_dir = frappe.get_app_path("masar_diwan", "masar_diwan", "workflow")
		if not os.path.isdir(workflow_dir):
			return
		for folder in sorted(os.listdir(workflow_dir)):
			path = os.path.join(workflow_dir, folder, f"{folder}.json")
			if os.path.exists(path):
				import_file_by_path(path)
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="masar_diwan: failed to ensure Workflows")


def ensure_workflow_states():
	"""Found 2026-09-22 via a real live-browser session on `diwan.local`: opening
	a brand-new `Internal Mail Movement` as a non-Administrator role threw a
	misleading 403 ("does not have doctype access ... for document Workflow
	State"), and the same action as Administrator (who bypasses the role-
	permission wall) revealed the real error underneath it: `Workflow State
	In Transit not found`.

	Root cause, confirmed by reading `frappe/desk/form/meta.py::load_workflows()`
	directly: every time a doctype's form meta is loaded, Frappe fetches a real
	`Workflow State` document (`frappe.get_doc("Workflow State", state)`) for
	each state in that doctype's active workflow, purely to read its display
	`style` (Success/Danger/Warning/...). Desk's own "New Workflow State"
	dialog auto-creates this record the moment a Workflow is saved *from the
	Desk UI* - but a Workflow imported via `ensure_workflows()`'s JSON importer
	(see its own docstring above) never goes through that save path, so it
	never creates the matching `Workflow State` rows. `diwan.local` was missing
	all three of this workflow's states outright (`Draft`/`In Transit`/
	`Received`); `bob.local` only avoided the same failure because `Draft`
	happened to already exist as a side effect of an older, unrelated
	workflow sharing that same state name - masking the gap there, not fixing
	it. Any future workflow (this app's own, or a state name that doesn't
	happen to collide with an existing one) would hit the same failure again.

	Fixed the same way `ensure_workflows()` fixes its own gap: generic,
	idempotent, re-run on every migrate. Reads every state of every Workflow
	this app owns and creates whichever `Workflow State` records are missing,
	rather than hardcoding the two states that happened to be missing when
	this was first diagnosed.
	"""
	# A Workflow's own `states` child table (`Workflow Document State`) has no
	# style field of its own - display style belongs solely to the separate
	# `Workflow State` master this function creates, referenced only by
	# `state`'s Link. This app's workflow JSON files never carried style
	# information to begin with, so there's nothing to read one from; this is
	# a best-effort default map for the state names this app's own 3
	# workflows are known to use (matching the styling `bob.local` already had
	# for the states that happened to pre-exist there), falling back to
	# "Primary" for anything not listed so a genuinely new/renamed state still
	# gets created instead of silently failing.
	STATE_STYLES = {
		"Draft": "Inverse",
		"In Transit": "Warning",
		"Received": "Success",
		"Pending Review": "Warning",
		"Under Review": "Warning",
		"Needs Revision": "Warning",
		"Approved & Numbered": "Success",
		"Rejected": "Danger",
		"Pending Delivery": "Warning",
		"Delivered": "Primary",
		"Receipt Confirmed": "Success",
		"Completed": "Success",
		"Archived": "Info",
		"Referred / In Progress": "Primary",
	}
	try:
		workflow_dir = frappe.get_app_path("masar_diwan", "masar_diwan", "workflow")
		if not os.path.isdir(workflow_dir):
			return
		for folder in sorted(os.listdir(workflow_dir)):
			path = os.path.join(workflow_dir, folder, f"{folder}.json")
			if not os.path.exists(path):
				continue
			with open(path) as f:
				workflow = json.load(f)
			for state_row in workflow.get("states", []):
				state_name = state_row.get("state")
				if state_name and not frappe.db.exists("Workflow State", state_name):
					frappe.get_doc(
						{
							"doctype": "Workflow State",
							"workflow_state_name": state_name,
							"style": STATE_STYLES.get(state_name, "Primary"),
						}
					).insert(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.log_error(title="masar_diwan: failed to ensure Workflow States")


DYNAMIC_FIELD_TARGET_DOCTYPES = ["Correspondence Request", "Correspondence"]
DYNAMIC_FIELD_PREFIX = "csf_"


def ensure_dynamic_fields():
	"""Self-healing sync for the per-category dynamic-field engine, matching
	ensure_workflows()/ensure_workflow_states()'s own pattern: a user defines
	fields in a simple screen (Correspondence Category's own `dynamic_fields`
	child table) instead of touching Customize Form directly, and this turns
	each active row into a real Custom Field on both Correspondence Request
	and Correspondence (mirrored so a value survives Approve & Register) -
	real columns, so reports/filters/print all work on them for free.

	Read every category once, group its active rows by `fieldname_slug`
	(several categories can legitimately share one column via the "Reuse
	Existing Field" mode - see correspondence_category.py's own validate()),
	and build one Custom Field per distinct slug, visible/mandatory exactly
	when the request's *effective* category selection - its
	correspondence_sub_category if set, else its own correspondence_category
	when that one has no children - is one of the categories using that
	slug. Idempotent: compares the Custom Field's actual stored properties
	against what's wanted and only writes when they differ, the same
	discipline as ensure_workflows()'s own hash/timestamp check.
	"""
	try:
		by_slug = {}
		for category_name in frappe.get_all("Correspondence Category", pluck="name"):
			category = frappe.get_cached_doc("Correspondence Category", category_name)
			for row in category.dynamic_fields:
				if not row.fieldname_slug:
					continue
				entry = by_slug.setdefault(
					row.fieldname_slug,
					{"row": row, "active_categories": []},
				)
				if row.is_active:
					entry["active_categories"].append(category_name)

		for slug, info in by_slug.items():
			_ensure_dynamic_custom_field(slug, info["row"], info["active_categories"])

		for doctype in DYNAMIC_FIELD_TARGET_DOCTYPES:
			frappe.clear_cache(doctype=doctype)
	except Exception:
		frappe.log_error(title="masar_diwan: failed to ensure dynamic fields")


def _ensure_dynamic_custom_field(slug, row, active_categories):
	if row.fieldtype == "Link" and row.link_scope == "erpnext":
		if not frappe.db.exists("DocType", row.options):
			frappe.log_error(
				title="masar_diwan: dynamic field skipped, target DocType missing",
				message=(
					f"Field '{row.label}' (csf_{slug}) targets '{row.options}', which doesn't exist on this "
					"site (likely no ERPNext installed here). Skipped this sync - will retry on the next "
					"migrate once/if the target DocType exists."
				),
			)
			return

	fieldname = f"{DYNAMIC_FIELD_PREFIX}{slug}"
	visible_categories_json = frappe.as_json(active_categories, indent=None) if active_categories else "[]"
	condition = f"eval:{visible_categories_json}.includes(doc.correspondence_sub_category || doc.correspondence_category)"

	for doctype in DYNAMIC_FIELD_TARGET_DOCTYPES:
		# On Correspondence, the request's own category/sub-category context
		# no longer exists as such a field - the value was already copied
		# over at Approve & Register (see register_correspondence()). Shown
		# unconditionally there rather than reconstructing the same
		# condition against a field this doctype doesn't have.
		depends_on = condition if doctype == "Correspondence Request" else ("eval:1" if active_categories else "eval:0")
		mandatory_depends_on = depends_on if row.reqd and active_categories else None

		wanted = {
			"label": row.label,
			"fieldtype": row.fieldtype,
			"options": row.options,
			"depends_on": depends_on,
			"mandatory_depends_on": mandatory_depends_on,
			"insert_after": "resulting_correspondence" if doctype == "Correspondence Request" else "confidentiality",
		}

		existing_name = frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
		if not existing_name:
			cf = frappe.get_doc({"doctype": "Custom Field", "dt": doctype, "fieldname": fieldname, **wanted})
			cf.insert(ignore_permissions=True)
			continue

		current = frappe.db.get_value(
			"Custom Field", existing_name, list(wanted.keys()), as_dict=True
		)
		if any(current.get(k) != v for k, v in wanted.items()):
			cf = frappe.get_doc("Custom Field", existing_name)
			cf.update(wanted)
			cf.save(ignore_permissions=True)

	frappe.db.commit()


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
	`Correspondence Request.requesting_department`, and
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


def ensure_department_read_access():
	"""When ERPNext provides the real `Department` doctype, its own shipped
	DocPerm rows only grant read to `Academics User`/`HR User`/`HR Manager` -
	none of masar_diwan's own roles. Confirmed as a real, practical gap
	2026-09-22: `test.diwan@masar-diwan.local` (Diwan Officer, no HR role)
	got a genuine `PermissionError` from `frappe.desk.search.search_link`
	trying to use the Department field's own link-search dropdown on
	`bob.local` - not a hypothetical, reproduced live over HTTP. Fixed via
	`Custom DocPerm` (Frappe's own standard mechanism for adding a
	site-local permission row without editing another app's shipped
	DocPerm) rather than touching ERPNext's own `department.json` - read
	only, nothing else (masar_diwan never creates/edits a Department, ERPNext-
	backed or not - that stays HR's job on a site that has ERPNext).

	No-ops immediately when ERPNext isn't installed - our own fallback
	`Department` (see `_create_masar_department_doctype()`) already grants
	these same roles read access natively, in its own DocPerm, no Custom
	DocPerm needed there.
	"""
	try:
		if "erpnext" not in frappe.get_installed_apps():
			return
		if frappe.db.get_value("DocType", "Department", "module") != "Setup":
			return  # not ERPNext's real Department (e.g. mid-transition) - leave it to the other hooks

		for role in DEPARTMENT_READ_ROLES:
			if frappe.db.exists("Custom DocPerm", {"parent": "Department", "role": role, "read": 1}):
				continue
			frappe.get_doc(
				{
					"doctype": "Custom DocPerm",
					"parent": "Department",
					"parenttype": "DocType",
					"parentfield": "permissions",
					"role": role,
					"read": 1,
				}
			).insert(ignore_permissions=True)
		frappe.db.commit()
		frappe.clear_cache(doctype="Department")
	except Exception:
		frappe.log_error(title="masar_diwan: failed to ensure Department read access")


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
