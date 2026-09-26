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

// Scope the shared treatment to Diwan routes; other ERPNext apps keep their UI.
(function () {
	const guidance = {
		"Correspondence": __("Register correspondence, assign responsibility, and follow its progress."),
		"Correspondence Request": __("Prepare a draft for the Diwan team. An official reference is assigned after approval."),
		"Internal Mail Movement": __("Record the sending and receiving departments, then track the handoff."),
		"Delivery Sheet": __("Group correspondence for delivery and record the recipient's proof of receipt."),
		"Envelope": __("Group documents in an envelope and link it to a delivery sheet when ready."),
		"Correspondence Category": __("Organize categories and define the additional fields required for each request."),
		"Correspondence Type": __("Define a correspondence type and the prefix used for its reference numbers."),
		"Confidentiality Level": __("Define who can read documents at this confidentiality level."),
		"Document Access Profile": __("Configure department access, confidentiality, numbering, and search for a document type."),
		"Correspondence Settings": __("Manage reference numbering and the response to restricted QR scans."),
		"Access Log Entry": __("History of document access and actions, including denied attempts."),
	};
	const statusGuidance = {
		"Draft": __("Complete the required fields and save your draft before taking the next action."),
		"Pending Review": __("Submitted to the Diwan team and waiting for review."),
		"Under Review": __("Review the details and use the available workflow actions to continue."),
		"Needs Revision": __("Read the decision note, update the request, and submit it again."),
		"Rejected": __("Read the decision note for the reason this request was rejected."),
		"Approved": __("Approved for registration. Select a Correspondence Type and use Register to issue the reference number."),
		"Approved & Numbered": __("The request has been registered. Open the resulting correspondence to follow its progress."),
		"Referred / In Progress": __("Follow up with the current owner and record progress before completion."),
		"Completed": __("Work is complete. Review the history and related documents."),
		"In Transit": __("The receiving department can confirm receipt after the handoff."),
		"Received": __("Receipt has been recorded. Review the recipient and receipt time."),
		"Pending Delivery": __("Review the recipient, address, and document list before dispatch."),
		"Delivered": __("Attach the signed receipt before confirming receipt."),
		"Receipt Confirmed": __("Delivery is complete and proof of receipt is recorded."),
		"Open": __("Add the enclosed documents and link a delivery sheet when ready."),
		"Sent": __("Use the tracking reference to follow this envelope."),
		"Archived": __("This record is archived for reference."),
	};
	const reports = ["Overdue Correspondence", "Correspondence Completion Time", "Access Log Report"];
	const pages = ["correspondence-request-new", "correspondence-track"];
	function scopeRoute() {
		const route = frappe.get_route() || [];
		const active = (["Form", "List", "Tree"].includes(route[0]) && Object.hasOwn(guidance, route[1])) ||
			(route[0] === "query-report" && reports.includes(route[1])) || pages.includes(route[0]) ||
			(["Workspaces", "workspace"].includes(route[0]) && ["Masar Diwan", "masar-diwan"].includes(route[1]));
		document.body.classList.toggle("md-desk", Boolean(active));
	}
	$(document).on("app_ready", function () {
		frappe.router.on("change", scopeRoute);
		scopeRoute();
	});
	Object.entries(guidance).forEach(([doctype, description]) => {
		frappe.ui.form.on(doctype, {
			refresh(frm) {
				const host = frm.layout.wrapper;
				host.find(".md-form-guide").remove();
				const escape = frappe.utils.escape_html;
				const hint = statusGuidance[frm.doc.status];
				const guide = $('<section class="md-form-guide"></section>');
				guide.html(`<div class="md-form-guide__title">${escape(__(doctype))}</div>
					<p>${escape(description)}</p>${hint ? `<p class="md-form-guide__next">${escape(hint)}</p>` : ""}`);
				host.prepend(guide);
			},
		});
	});
})();
