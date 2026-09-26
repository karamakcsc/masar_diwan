// Shared chrome behaviour for the three masar_diwan portals. Loaded per-page
// (not globally) alongside diwan-portal.css - see each www/diwan/* page.

window.diwanPortal = (function () {
	function initDrawer() {
		var hamburger = document.querySelector("[data-diwan-hamburger]");
		var drawer = document.querySelector("[data-diwan-drawer]");
		var scrim = document.querySelector("[data-diwan-scrim]");
		if (!hamburger || !drawer || !scrim) return;

		function open() {
			drawer.classList.add("is-open");
			scrim.classList.add("is-open");
		}
		function close() {
			drawer.classList.remove("is-open");
			scrim.classList.remove("is-open");
		}
		hamburger.addEventListener("click", open);
		scrim.addEventListener("click", close);
		drawer.querySelectorAll("a").forEach(function (a) {
			a.addEventListener("click", close);
		});
	}

	// Status string -> pill CSS suffix. The visible label is always the raw
	// status run through __() at render time (ar.csv already translates every
	// one of these), never baked into this map, so it stays correct
	// regardless of the active session language.
	var REQUEST_STATUS_CLASS = {
		"Draft": "draft",
		"Pending Review": "pending",
		"Under Review": "review",
		"Needs Revision": "revision",
		"Rejected": "rejected",
		"Approved": "approved",
		"Approved & Numbered": "approved"
	};

	var CORRESPONDENCE_STATUS_CLASS = {
		"Draft": "draft",
		"Under Review": "review",
		"Referred / In Progress": "pending",
		"Completed": "approved",
		"Archived": "draft"
	};

	function statusPillHtml(status, map) {
		map = map || REQUEST_STATUS_CLASS;
		var cls = map[status] || "draft";
		return (
			'<span class="indicator-pill indicator-pill--' + cls + '">' +
			'<span class="dot"></span>' +
			frappe.utils.escape_html(__(status || "")) +
			"</span>"
		);
	}

	function confidentialityPillHtml(confidentiality) {
		if (!confidentiality || confidentiality === "Normal") return "";
		var cls = confidentiality === "Highly Confidential" ? "highly-confidential" : "confidential";
		return (
			'<span class="indicator-pill indicator-pill--' + cls + '">' +
			'<span class="dot"></span>' +
			frappe.utils.escape_html(__(confidentiality)) +
			"</span>"
		);
	}

	// The real Correspondence Workflow states, in order (see CLAUDE.md /
	// correspondence_workflow.json) - used to render the horizontal
	// done/current/upcoming workflow bar on a found-and-authorized Track
	// result (both /track and the Desk "Correspondence Tracking" page).
	var CORRESPONDENCE_WORKFLOW_STEPS = ["Draft", "Under Review", "Referred / In Progress", "Completed", "Archived"];

	function correspondenceHstepperHtml(status) {
		var idx = Math.max(0, CORRESPONDENCE_WORKFLOW_STEPS.indexOf(status));
		return (
			'<div class="diwan-hstepper">' +
			CORRESPONDENCE_WORKFLOW_STEPS.map(function (step, i) {
				var cls = i < idx ? "is-done" : i === idx ? "is-current" : "";
				var mark = i < idx ? "&#10003;" : String(i + 1);
				return (
					'<div class="diwan-hstepper__step ' + cls + '">' +
					'<div class="diwan-hstepper__dot">' + mark + "</div>" +
					'<div class="diwan-hstepper__label">' + frappe.utils.escape_html(__(step)) + "</div>" +
					"</div>"
				);
			}).join("") +
			"</div>"
		);
	}

	// Small inline lock glyph for the "found but restricted" notice - no new
	// icon asset, same currentColor-stroke convention as diwan_shell.html's
	// own nav_icon() macro.
	var LOCK_ICON_SVG =
		'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">' +
		'<rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>';

	document.addEventListener("DOMContentLoaded", initDrawer);

	return {
		statusPillHtml: statusPillHtml,
		confidentialityPillHtml: confidentialityPillHtml,
		correspondenceHstepperHtml: correspondenceHstepperHtml,
		LOCK_ICON_SVG: LOCK_ICON_SVG,
		REQUEST_STATUS_CLASS: REQUEST_STATUS_CLASS,
		CORRESPONDENCE_STATUS_CLASS: CORRESPONDENCE_STATUS_CLASS
	};
})();
