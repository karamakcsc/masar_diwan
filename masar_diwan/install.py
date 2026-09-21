import frappe

ROLES = [
	"Correspondence Employee",
	"Department Head",
	"Diwan Officer",
	"Senior Management",
	"Portal Tracking User",
]


def after_install():
	create_roles()
	ensure_workspace_sidebar()
	ensure_desktop_icon()


def after_migrate():
	ensure_workspace_sidebar()
	ensure_desktop_icon()


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
