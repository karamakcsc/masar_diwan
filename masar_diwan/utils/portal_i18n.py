"""Supply this app's messages to the website's JavaScript translator."""

import frappe
from frappe.translate import get_translations_from_apps


def get_portal_messages():
	# Website boot data does not include Desk's message dictionary. Keep this
	# scoped to Diwan, and honor site translation overrides through frappe._.
	messages = get_translations_from_apps(frappe.local.lang, apps=["masar_diwan"])
	return {key: frappe._(key) for key in messages}
