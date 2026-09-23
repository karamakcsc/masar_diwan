// Copyright (c) 2026, Masar and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Correspondence Request", {
// 	refresh(frm) {

// 	},
// });



frappe.ui.form.on('Correspondence Request', {
    refresh: function(frm) {

        frm.set_query('correspondence_sub_category', function(doc) {
            return {
                filters: [
                    ['Correspondence Category', 'parent_correspondence_category', '=', doc.correspondence_category],
                    ['Correspondence Category', 'is_group', '=', 0]
                ]
            };
        });

    }
});