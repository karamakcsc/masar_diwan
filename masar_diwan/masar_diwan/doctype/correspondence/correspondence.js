// Copyright (c) 2026, Masar and contributors
// For license information, please see license.txt

frappe.ui.form.on("Correspondence", {
	onload(frm) {
		if (frm.is_new()) {
			return;
		}
		frappe.call({
			method: "masar_diwan.access_log.log_view",
			args: {
				reference_doctype: frm.doctype,
				reference_name: frm.docname,
				channel: "Desk",
			},
		});
	},
});
