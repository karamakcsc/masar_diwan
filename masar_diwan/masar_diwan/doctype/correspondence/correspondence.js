// Copyright (c) 2026, Masar and contributors
// For license information, please see license.txt

// Registered-correspondence view additions (QR card, source-request banner,
// workflow stepper) - purely presentational, built on fields that already
// exist (qr_code, source_request, owner/creation, status). No new field was
// added: there is no dedicated "registered by" field, so that card uses the
// standard owner/creation meta fields, which are already accurate (
// register_correspondence() inserts as the approving Diwan Officer's own
// session, not a generic system user - confirmed live).
//
// The workflow-stepper rendering itself now lives in the shared
// window.masarDiwanDesk helper (public/js/masar_diwan-desk.js, loaded
// app-wide) rather than being hand-rolled again in this file - see that
// file's header comment for the duplication this replaced.

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
		// Same cascading filter Correspondence Request's own client script
		// already uses for this exact field pair - kept here rather than in
		// link_filters (which is Desk-form-JS-only anyway, so this Client
		// Script is already the only real enforcement layer) so both
		// doctypes' pickers behave identically. Applies regardless of
		// is_new(): a direct Correspondence's category is editable up until
		// it's locked by a source_request (see correspondence.py's own
		// validate()), not just at creation time.
		frm.set_query("correspondence_sub_category", function (doc) {
			return {
				filters: [
					["Correspondence Category", "parent_correspondence_category", "=", doc.correspondence_category],
					["Correspondence Category", "is_group", "=", 0],
				],
			};
		});

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
				${window.masarDiwanDesk.renderCorrespondenceStepper(frm.doc.status)}
			</div>
		</div>
	`;

	frm.dashboard.add_section(html);
}
