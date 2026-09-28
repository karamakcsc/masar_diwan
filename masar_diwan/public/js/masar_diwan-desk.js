// Shared Desk-side helpers for masar_diwan, loaded app-wide via hooks.py's
// app_include_js. This exists to close a real duplication found in a code
// audit: the same 5-state Correspondence Workflow stepper used to be
// hand-rolled independently in THREE places -
//   1. public/js/diwan-portal.js (correspondenceHstepperHtml) - used only by
//      the www/track portal page, not reachable from Desk JS at all.
//   2. masar_diwan/doctype/correspondence/correspondence.js
//      (render_workflow_stepper_html, inline-styled).
//   3. masar_diwan/page/correspondence_track/correspondence_track.js
//      (render_hstepper_html, class-based).
// diwan-portal.js can't be reused here directly - it's a www/-only static
// asset, never loaded on the Desk side - so this file is the Desk-side
// equivalent, loaded once app-wide instead of copy-pasted per page/form.
// Both of the call sites above now call window.masarDiwanDesk.
// renderCorrespondenceStepper() instead of keeping their own copy. The
// matching CSS (.md-hstepper*) lives in public/css/masar_diwan-desk.css,
// already loaded app-wide alongside this file.

window.masarDiwanDesk = (function () {
	// The real Correspondence Workflow states, in order - see CLAUDE.md /
	// correspondence_workflow.json. Read once, from one place, instead of
	// three separately hardcoded copies.
	var CORRESPONDENCE_WORKFLOW_STEPS = [
		"Draft",
		"Under Review",
		"Referred / In Progress",
		"Completed",
		"Archived",
	];

	function renderCorrespondenceStepper(status) {
		var idx = Math.max(0, CORRESPONDENCE_WORKFLOW_STEPS.indexOf(status));
		return (
			'<div class="md-hstepper">' +
			CORRESPONDENCE_WORKFLOW_STEPS.map(function (step, i) {
				var cls = i < idx ? "is-done" : i === idx ? "is-current" : "";
				var mark = i < idx ? "&#10003;" : String(i + 1);
				return (
					'<div class="md-hstepper__step ' + cls + '">' +
					'<div class="md-hstepper__dot">' + mark + "</div>" +
					'<div class="md-hstepper__label">' + frappe.utils.escape_html(__(step)) + "</div>" +
					"</div>"
				);
			}).join("") +
			"</div>"
		);
	}

	// The "Additional Fields" section (masar_diwan/install.py's
	// ensure_dynamic_fields()) lays out every dynamic field from every
	// Correspondence Category in ONE shared, globally-alphabetical
	// two-column split - correct at that global level, but a single
	// category's own visible subset (the only fields depends_on lets a
	// real Correspondence/Correspondence Request actually show) can still
	// land lopsided across the two columns purely by where its fields
	// happened to fall in the *global* alphabetical order, since column
	// assignment is a static property of each Custom Field, not something
	// recomputed per visible category (real screenshot, 2026-09-29: a
	// category with 3 fields showed 1 in column 1 and 2 in column 2).
	//
	// Reflowed here instead, client-side, after every render/dependency
	// re-evaluation: gather only the currently-VISIBLE csf_ fields (in the
	// form's own field_order, so the alphabetical intent is preserved),
	// then redistribute them 1st/3rd/5th.. into column 1 and 2nd/4th/6th..
	// into column 2 - moving already-rendered control wrappers between the
	// two real `.form-column` containers Frappe itself created for the
	// Section/Column Break pair, not re-rendering anything.
	function reflowDynamicFieldColumns(frm) {
		var columnBreakField = frm.fields_dict["csf_column_break"];
		if (!columnBreakField || !columnBreakField.$wrapper) return;
		var col2 = columnBreakField.$wrapper.closest(".form-column");
		if (!col2.length) return;
		var col1 = col2.prev(".form-column");
		if (!col1.length) return;

		var order = frm.meta.fields.map(function (df) {
			return df.fieldname;
		});
		var visible = Object.keys(frm.fields_dict)
			.filter(function (fieldname) {
				if (fieldname.indexOf("csf_") !== 0) return false;
				if (fieldname === "csf_section" || fieldname === "csf_column_break") return false;
				var field = frm.fields_dict[fieldname];
				return field.$wrapper && !field.df.hidden_due_to_dependency && !field.df.hidden;
			})
			.map(function (fieldname) {
				return frm.fields_dict[fieldname];
			})
			.sort(function (a, b) {
				return order.indexOf(a.df.fieldname) - order.indexOf(b.df.fieldname);
			});

		visible.forEach(function (field, i) {
			(i % 2 === 0 ? col1 : col2).append(field.$wrapper);
		});
	}

	return {
		CORRESPONDENCE_WORKFLOW_STEPS: CORRESPONDENCE_WORKFLOW_STEPS,
		renderCorrespondenceStepper: renderCorrespondenceStepper,
		reflowDynamicFieldColumns: reflowDynamicFieldColumns,
	};
})();
