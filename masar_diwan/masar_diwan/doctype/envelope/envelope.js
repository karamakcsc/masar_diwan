frappe.ui.form.on("Envelope", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Track Envelope"), () => {
			window.open("/track?ref=" + encodeURIComponent(frm.doc.name), "_blank", "noopener");
		});
	},
});
