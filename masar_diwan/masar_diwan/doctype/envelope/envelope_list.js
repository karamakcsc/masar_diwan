// Consistent lifecycle indicators; the filter preserves the exact workflow value.
frappe.listview_settings["Envelope"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const colors = {"Open": "orange", "Sent": "blue", "Archived": "gray"};
		return [__(doc.status || ""), colors[doc.status] || "gray", "status,=," + doc.status];
	},
};
