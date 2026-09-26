// Consistent lifecycle indicators; the filter preserves the exact workflow value.
frappe.listview_settings["Delivery Sheet"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const colors = {"Pending Delivery": "orange", "Delivered": "blue", "Receipt Confirmed": "green"};
		return [__(doc.status || ""), colors[doc.status] || "gray", "status,=," + doc.status];
	},
};
