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


def after_migrate():
	ensure_workspace_sidebar()


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
