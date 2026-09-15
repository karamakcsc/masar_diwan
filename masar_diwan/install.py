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


def create_roles():
	for role_name in ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		role = frappe.new_doc("Role")
		role.role_name = role_name
		role.desk_access = 0 if role_name == "Portal Tracking User" else 1
		role.insert(ignore_permissions=True)
