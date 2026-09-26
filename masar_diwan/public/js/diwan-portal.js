// Shared chrome behaviour for the three masar_diwan portals. Loaded per-page
// (not globally) alongside diwan-portal.css - see each www/diwan/* page.

window.diwanPortal = (function () {
	function initDrawer() {
		const hamburger = document.querySelector("[data-diwan-hamburger]");
		const drawer = document.querySelector("[data-diwan-drawer]");
		const scrim = document.querySelector("[data-diwan-scrim]");
		const shell = document.querySelector(".diwan-shell");
		if (!hamburger || !drawer || !scrim || !shell) return;
		function close(restoreFocus = true) {
			drawer.classList.remove("is-open");
			scrim.classList.remove("is-open");
			drawer.hidden = true;
			drawer.inert = true;
			shell.inert = false;
			document.body.classList.remove("diwan-drawer-open");
			hamburger.setAttribute("aria-expanded", "false");
			if (restoreFocus) hamburger.focus();
		}
		hamburger.addEventListener("click", function () {
			drawer.hidden = false;
			drawer.inert = false;
			drawer.classList.add("is-open");
			scrim.classList.add("is-open");
			hamburger.setAttribute("aria-expanded", "true");
			shell.inert = true;
			document.body.classList.add("diwan-drawer-open");
			drawer.querySelector("[data-diwan-close]").focus();
		});
		scrim.addEventListener("click", () => close());
		drawer.querySelector("[data-diwan-close]").addEventListener("click", () => close());
		drawer.addEventListener("keydown", function (event) {
			if (event.key === "Escape") { event.preventDefault(); close(); }
			if (event.key !== "Tab") return;
			const items = Array.from(drawer.querySelectorAll('button, a[href]:not([tabindex="-1"])'));
			const first = items[0], last = items[items.length - 1];
			if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
			else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
		});
		window.matchMedia("(min-width: 901px)").addEventListener("change", event => {
			if (event.matches && !drawer.hidden) close(false);
		});
	}

	function initTables() {
		document.querySelectorAll(".diwan-table-scroll").forEach(function (wrapper, index) {
			const table = wrapper.querySelector("table");
			if (table.querySelector(".row-select")) return;
			const rows = Array.from(table.querySelectorAll("tbody > tr"));
			if (!rows.length) return;
			const tools = document.createElement("div");
			tools.className = "diwan-table-tools";
			const label = document.createElement("label");
			label.htmlFor = "diwan-table-filter-" + index;
			label.textContent = __("Filter loaded rows");
			const input = document.createElement("input");
			input.type = "search";
			input.id = label.htmlFor;
			const count = document.createElement("span");
			count.className = "diwan-table-count";
			count.setAttribute("role", "status");
			tools.append(label, input, count);
			wrapper.before(tools);
			const empty = document.createElement("div");
			empty.className = "diwan-empty";
			empty.textContent = __("No matching rows. Try another search.");
			empty.hidden = true;
			wrapper.after(empty);
			function filter() {
				const query = input.value.trim().toLocaleLowerCase();
				let visible = 0;
				rows.forEach(row => {
					row.hidden = !row.textContent.toLocaleLowerCase().includes(query);
					if (!row.hidden) visible++;
				});
				count.textContent = __("{0} of {1} rows", [visible, rows.length]);
				empty.hidden = visible !== 0;
			}
			input.addEventListener("input", filter);
			filter();
		});
	}

	function initLanguageLinks() {
		document.querySelectorAll(".diwan-navbar__lang a").forEach(link => {
			const language = new URL(link.href).searchParams.get("_lang");
			const url = new URL(window.location.href);
			url.searchParams.set("_lang", language);
			link.href = url.pathname + url.search + url.hash;
			link.lang = language;
			link.setAttribute("aria-label", language === "ar" ? "العربية" : "English");
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

	frappe.ready(function () {
		initDrawer();
		initLanguageLinks();
		initTables();
	});

	return {
		statusPillHtml: statusPillHtml,
		confidentialityPillHtml: confidentialityPillHtml,
		correspondenceHstepperHtml: correspondenceHstepperHtml,
		LOCK_ICON_SVG: LOCK_ICON_SVG,
		REQUEST_STATUS_CLASS: REQUEST_STATUS_CLASS,
		CORRESPONDENCE_STATUS_CLASS: CORRESPONDENCE_STATUS_CLASS
	};
})();
