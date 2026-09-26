// Consistent lifecycle indicators; the filter preserves the exact workflow value.
frappe.listview_settings["Correspondence"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const colors = {"Draft": "gray", "Under Review": "blue", "Referred / In Progress": "orange", "Completed": "green", "Archived": "gray"};
		return [__(doc.status || ""), colors[doc.status] || "gray", "status,=," + doc.status];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Track Correspondence"), () => frappe.set_route("correspondence-track"));
	},
};
