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

	return {
		CORRESPONDENCE_WORKFLOW_STEPS: CORRESPONDENCE_WORKFLOW_STEPS,
		renderCorrespondenceStepper: renderCorrespondenceStepper,
	};
})();
