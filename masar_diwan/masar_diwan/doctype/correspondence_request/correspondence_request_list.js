// Consistent lifecycle indicators; the filter preserves the exact workflow value.
frappe.listview_settings["Correspondence Request"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const colors = {"Draft": "gray", "Pending Review": "orange", "Under Review": "blue", "Needs Revision": "yellow", "Rejected": "red", "Approved": "blue", "Approved & Numbered": "green"};
		return [__(doc.status || ""), colors[doc.status] || "gray", "status,=," + doc.status];
	},
	onload(listview) {
		if (frappe.model.can_create("Correspondence Request")) listview.page.add_inner_button(__("Guided request"), () => frappe.set_route("correspondence-request-new"));
	},
};
