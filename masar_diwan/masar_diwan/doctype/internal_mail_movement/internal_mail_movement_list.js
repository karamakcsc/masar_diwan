// Consistent lifecycle indicators; the filter preserves the exact workflow value.
frappe.listview_settings["Internal Mail Movement"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const colors = {"Draft": "gray", "In Transit": "orange", "Received": "green"};
		return [__(doc.status || ""), colors[doc.status] || "gray", "status,=," + doc.status];
	},
};
