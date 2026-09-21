// Copyright (c) 2026, Masar and contributors
// For license information, please see license.txt

// Registered-correspondence view additions (QR card, source-request banner,
// workflow stepper) - purely presentational, built on fields that already
// exist (qr_code, source_request, owner/creation, status). No new field was
// added: there is no dedicated "registered by" field, so that card uses the
// standard owner/creation meta fields, which are already accurate (
// register_correspondence() inserts as the approving Diwan Officer's own
// session, not a generic system user - confirmed live).
const CORRESPONDENCE_WORKFLOW_STEPS = [
	"Draft",
	"Under Review",
	"Referred / In Progress",
	"Completed",
	"Archived",
];

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

	refresh(frm) {
		if (frm.is_new()) {
			return;
		}
		render_source_request_banner(frm);
		render_registered_dashboard_section(frm);
	},
});

function render_source_request_banner(frm) {
	if (!frm.doc.source_request) return;
	const url = `/app/correspondence-request/${encodeURIComponent(frm.doc.source_request)}`;
	frm.dashboard.set_headline_alert(
		`${__("Registered from request")} <a href="${url}">${frappe.utils.escape_html(frm.doc.source_request)}</a>`,
		"blue"
	);
}

function render_workflow_stepper_html(current_status) {
	// Colors reference the shared --md-* identity tokens (masar_diwan-desk.css,
	// loaded app-wide via hooks.py app_include_css): done = --md-success,
	// current = --md-brand, upcoming = neutral gray. Presentational only -
	// the steps themselves are still read verbatim from the real Correspondence
	// Workflow states (see CORRESPONDENCE_WORKFLOW_STEPS above), not guessed.
	const idx = Math.max(0, CORRESPONDENCE_WORKFLOW_STEPS.indexOf(current_status));
	return `
		<div class="correspondence-registered-stepper" style="display:flex; align-items:flex-start;">
			${CORRESPONDENCE_WORKFLOW_STEPS.map((step, i) => {
				const done = i < idx;
				const active = i === idx;
				const circle_bg = done ? "var(--md-success, #187269)" : active ? "var(--md-brand, #1a375b)" : "var(--md-ink-100, #eff2f5)";
				const circle_color = done || active ? "#fff" : "rgba(17,24,39,.55)";
				const label_color = done || active ? "#111827" : "rgba(17,24,39,.55)";
				const label_weight = done || active ? "600" : "400";
				const line = i < CORRESPONDENCE_WORKFLOW_STEPS.length - 1
					? `<div style="flex:1; height:2px; background:${i < idx ? "var(--md-success, #187269)" : "var(--md-ink-100, #eff2f5)"}; margin-top:11px;"></div>`
					: "";
				return `
					<div style="display:flex; flex-direction:column; align-items:center; ${i === 0 ? "" : "flex:1;"}">
						<div style="width:22px; height:22px; border-radius:50%; background:${circle_bg}; color:${circle_color};
							display:flex; align-items:center; justify-content:center; font-size:11px;">
							${done ? "&#10003;" : i + 1}
						</div>
						<div style="font-size:11px; margin-top:4px; text-align:center; color:${label_color}; font-weight:${label_weight};">
							${__(step)}
						</div>
					</div>
					${line}
				`;
			}).join("")}
		</div>
	`;
}

function render_registered_dashboard_section(frm) {
	// Idempotent: remove any previously injected section before re-adding,
	// since refresh() fires again after every save/workflow transition and
	// the stepper/QR need to reflect the latest doc.status each time.
	frm.dashboard.parent.find(".correspondence-registered-section").remove();

	const qr_html = frm.doc.qr_code
		? `<img src="${frappe.utils.escape_html(frm.doc.qr_code)}" style="width:96px; height:96px; object-fit:contain; border:1px solid var(--md-ink-100, #eff2f5); border-radius:9px;">`
		: `<div class="text-muted small">${__("No QR code generated yet")}</div>`;

	const registered_by = frm.doc.owner
		? `${frappe.utils.escape_html(frm.doc.owner)} — ${frappe.datetime.str_to_user(frm.doc.creation)}`
		: "-";

	// frm.doc.name IS the reference number for a registered Correspondence
	// (e.g. "و-2026-0001") - wrapped in .ref-code to fix the Unicode bidi
	// rule W2 reversal (Arabic-letter prefix immediately followed by Latin
	// digits). See CLAUDE.md.
	const html = `
		<div class="correspondence-registered-section" style="display:flex; gap:24px; flex-wrap:wrap;
			padding:12px 15px; margin-bottom:10px; border:1px solid var(--md-ink-100, #eff2f5); border-radius:15px;
			box-shadow: 0 1px 2px rgba(10,20,40,.04), 0 6px 20px -6px rgba(10,20,40,.10);">
			<div style="text-align:center;">
				${qr_html}
				<div class="small text-muted mt-1 ref-code">${frappe.utils.escape_html(frm.doc.name)}</div>
			</div>
			<div style="flex:1; min-width:260px;">
				<div class="text-muted small mb-2">${__("Registered by")}: ${registered_by}</div>
				${render_workflow_stepper_html(frm.doc.status)}
			</div>
		</div>
	`;

	frm.dashboard.add_section(html);
}
