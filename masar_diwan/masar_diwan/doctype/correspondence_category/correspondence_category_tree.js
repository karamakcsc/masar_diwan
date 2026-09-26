frappe.treeview_settings["Correspondence Category"] = {
	title: __("Correspondence Categories"),
	onload(treeview) {
		const host = treeview.page.main;
		host.find(".md-category-tree-guide").remove();
		$('<section class="md-form-guide md-category-tree-guide"></section>')
			.append($('<div class="md-form-guide__title"></div>').text(__("Organize request categories")))
			.append($("<p></p>").text(__("Use groups to organize categories. Configure request fields on a leaf category. Open a category to manage its fields or disable it.")))
			.prependTo(host);
		treeview.page.add_inner_button(__("Category list"), () => frappe.set_route("List", "Correspondence Category"));
	},
};
