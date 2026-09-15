# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	summary = get_summary(data)
	return columns, data, None, None, summary


def get_columns():
	return [
		{"label": _("Date/Time"), "fieldname": "event_datetime", "fieldtype": "Datetime", "width": 160},
		{"label": _("User"), "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 160},
		{"label": _("Event Type"), "fieldname": "event_type", "fieldtype": "Data", "width": 110},
		{"label": _("Channel"), "fieldname": "channel", "fieldtype": "Data", "width": 80},
		{"label": _("Result"), "fieldname": "result", "fieldtype": "Data", "width": 80},
		{"label": _("Reason"), "fieldname": "reason", "fieldtype": "Data", "width": 160},
		{
			"label": _("Reference Type"),
			"fieldname": "reference_doctype",
			"fieldtype": "Link",
			"options": "DocType",
			"width": 130,
		},
		{"label": _("Reference"), "fieldname": "reference_name", "fieldtype": "Dynamic Link", "options": "reference_doctype", "width": 130},
		{"label": _("File"), "fieldname": "file_name", "fieldtype": "Data", "width": 130},
		{"label": _("IP Address"), "fieldname": "ip_address", "fieldtype": "Data", "width": 110},
		{"label": _("New IP"), "fieldname": "is_new_ip", "fieldtype": "Check", "width": 70},
		{"label": _("Device"), "fieldname": "device_info", "fieldtype": "Data", "width": 200},
	]


def get_data(filters):
	conditions = []
	values = {}

	simple_filters = ["user", "event_type", "channel", "result", "reference_doctype", "is_new_ip"]
	for f in simple_filters:
		if filters.get(f) not in (None, ""):
			conditions.append(f"`{f}` = %({f})s")
			values[f] = filters[f]

	if filters.get("from_date"):
		conditions.append("event_datetime >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("event_datetime <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where_clause = f"where {' and '.join(conditions)}" if conditions else ""

	return frappe.db.sql(
		f"""
		select
			event_datetime, user, event_type, channel, result, reason,
			reference_doctype, reference_name, file_name, ip_address,
			is_new_ip, device_info
		from `tabAccess Log Entry`
		{where_clause}
		order by event_datetime desc
		""",
		values,
		as_dict=True,
	)


def get_summary(data):
	total = len(data)
	success = sum(1 for d in data if d.result == "Success")
	denied = sum(1 for d in data if d.result == "Denied")
	new_ip = sum(1 for d in data if d.is_new_ip)

	return [
		{"label": _("Total Events"), "value": total, "datatype": "Int"},
		{"label": _("Successful"), "value": success, "datatype": "Int", "indicator": "Green"},
		{"label": _("Denied"), "value": denied, "datatype": "Int", "indicator": "Red"},
		{"label": _("From New IP"), "value": new_ip, "datatype": "Int", "indicator": "Orange"},
	]
