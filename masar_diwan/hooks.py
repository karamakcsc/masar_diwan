app_name = "masar_diwan"
app_title = "Masar Diwan"
app_publisher = "Masar"
app_description = "Correspondence, tracking and archiving system (Diwan) for ERPNext v16"
app_email = "claude@kcsc.com.jo"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "masar_diwan",
# 		"logo": "/assets/masar_diwan/logo.png",
# 		"title": "Masar Diwan",
# 		"route": "/masar_diwan",
# 		"has_permission": "masar_diwan.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/masar_diwan/css/masar_diwan.css"
# app_include_js = "/assets/masar_diwan/js/masar_diwan.js"

# include js, css files in header of web template
# web_include_css = "/assets/masar_diwan/css/masar_diwan.css"
# web_include_js = "/assets/masar_diwan/js/masar_diwan.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "masar_diwan/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "masar_diwan/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

jinja = {
	"methods": ["masar_diwan.utils.qrcode_utils.qr_data_uri"],
}

# Installation
# ------------

after_install = "masar_diwan.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "masar_diwan.uninstall.before_uninstall"
# after_uninstall = "masar_diwan.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "masar_diwan.utils.before_app_install"
# after_app_install = "masar_diwan.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "masar_diwan.utils.before_app_uninstall"
# after_app_uninstall = "masar_diwan.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "masar_diwan.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "masar_diwan.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["masar_diwan.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Correspondence": "masar_diwan.permissions.get_permission_query_conditions",
}

has_permission = {
	"Correspondence": "masar_diwan.permissions.has_permission",
}

# Access Log (Phase 6)
# --------------------
on_session_creation = "masar_diwan.access_log.log_login"

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"masar_diwan.tasks.all"
# 	],
# 	"daily": [
# 		"masar_diwan.tasks.daily"
# 	],
# 	"hourly": [
# 		"masar_diwan.tasks.hourly"
# 	],
# 	"weekly": [
# 		"masar_diwan.tasks.weekly"
# 	],
# 	"monthly": [
# 		"masar_diwan.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "masar_diwan.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "masar_diwan.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "masar_diwan.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "masar_diwan.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["masar_diwan.utils.before_request"]
# after_request = ["masar_diwan.utils.after_request"]

# Job Events
# ----------
# before_job = ["masar_diwan.utils.before_job"]
# after_job = ["masar_diwan.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"masar_diwan.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

# Fixtures
# --------
fixtures = [
	{
		"doctype": "Role",
		"filters": [
			[
				"name",
				"in",
				[
					"Correspondence Employee",
					"Department Head",
					"Diwan Officer",
					"Senior Management",
					"Portal Tracking User",
				],
			]
		],
	},
	{"doctype": "Correspondence Type"},
	{"doctype": "Correspondence Category"},
]

