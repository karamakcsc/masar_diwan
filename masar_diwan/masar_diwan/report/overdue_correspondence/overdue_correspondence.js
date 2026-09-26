// Filters use the same department/confidentiality rules as the document list.
frappe.query_reports["Overdue Correspondence"] = {
	filters: [
		{ fieldname: "department", label: __("Department"), fieldtype: "Link", options: "Department" },
		{ fieldname: "current_owner", label: __("Current Owner"), fieldtype: "Link", options: "User" },
		{ fieldname: "correspondence_type", label: __("Correspondence Type"), fieldtype: "Link", options: "Correspondence Type" },
		{ fieldname: "from_date", label: __("Follow-up From"), fieldtype: "Date" },
		{ fieldname: "to_date", label: __("Follow-up To"), fieldtype: "Date" },
	],
};
