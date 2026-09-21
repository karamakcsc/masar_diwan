// Copyright (c) 2026, Masar and contributors
// For license information, please see license.txt

frappe.query_reports["Access Log Report"] = {
	filters: [
		{
			fieldname: "user",
			label: __("User"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "event_type",
			label: __("Event Type"),
			fieldtype: "Select",
			options: "\nLogin\nView\nDownload\nQR Scan\nBarcode Scan\nTray Decision",
		},
		{
			fieldname: "channel",
			label: __("Channel"),
			fieldtype: "Select",
			options: "\nDesk\nPortal",
		},
		{
			fieldname: "result",
			label: __("Result"),
			fieldtype: "Select",
			options: "\nSuccess\nDenied",
		},
		{
			fieldname: "reference_doctype",
			label: __("Reference Document Type"),
			fieldtype: "Link",
			options: "DocType",
		},
		{
			fieldname: "is_new_ip",
			label: __("From New IP"),
			fieldtype: "Check",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Datetime",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Datetime",
		},
	],
};
