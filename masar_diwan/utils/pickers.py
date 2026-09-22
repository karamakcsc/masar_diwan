"""Small shared "list of options for a picker" helpers.

Previously `frappe.get_all("Correspondence Type", fields=["name", "title"])`
was written out independently in both www/diwan/queue/index.py and
www/diwan/tray/index.py - same query, same purpose (populating the type
dropdown before "Approve & Register"), two copies. Centralized here so a
future change to what a type picker needs (e.g. filtering out disabled
types) only has to happen in one place.
"""

import frappe


def correspondence_type_options():
	return frappe.get_all("Correspondence Type", fields=["name", "title"])
