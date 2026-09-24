frappe.pages["correspondence-track"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Correspondence Tracking"),
		single_column: true,
	});

	// Desk-side equivalent of the /track portal page for staff who'd rather
	// not leave the Desk SPA - calls the exact same masar_diwan.api.portal
	// functions the portal page uses, so permission/masking logic is never
	// duplicated between the two surfaces.

	inject_styles();

	const scan_field = page.add_field({
		fieldtype: "Data",
		fieldname: "ref",
		label: __("Scan or type a reference number"),
		change() {
			const ref = scan_field.get_value();
			if (ref) {
				lookup_ref(ref);
			}
		},
	});
	// Reference numbers are always LTR (e.g. "و-2026-0001") even in an RTL
	// session - see the .ref-code bidi fix in masar_diwan-desk.css. Applied
	// here to the editable input itself, not just to rendered output.
	if (scan_field.$input) {
		scan_field.$input.attr("dir", "ltr").addClass("ref-code").css({
			direction: "ltr",
			"unicode-bidi": "bidi-override",
		});
	}

	const filters_wrapper = $('<div class="row" style="margin: 10px 0;"></div>').appendTo(page.body);
	const search_text = page.add_field({
		fieldtype: "Data",
		fieldname: "search_text",
		label: __("Reference No / Subject"),
	});
	page.add_button(__("Search"), () => run_search(), { btn_type: "btn-primary" });

	const detail_wrapper = $('<div class="correspondence-track-detail"></div>').appendTo(page.body);
	const results_wrapper = $('<div class="correspondence-track-results" style="margin-top: 15px;"></div>').appendTo(
		page.body
	);

	function run_search() {
		frappe.call({
			method: "masar_diwan.api.portal.search_correspondence",
			args: { text: search_text.get_value() },
			callback(r) {
				render_results(r.message || []);
			},
		});
	}

	function render_results(rows) {
		results_wrapper.empty();
		if (!rows.length) {
			results_wrapper.html(`<div class="text-muted">${__("No results")}</div>`);
			return;
		}
		const table = $(`
			<table class="table table-bordered">
				<thead><tr>
					<th>${__("Reference No")}</th>
					<th>${__("Subject")}</th>
					<th>${__("Status")}</th>
					<th>${__("Department")}</th>
				</tr></thead>
				<tbody></tbody>
			</table>
		`).appendTo(results_wrapper);
		const tbody = table.find("tbody");
		rows.forEach((row) => {
			$(`<tr>
				<td><a href="#" class="track-row-link ref-code">${frappe.utils.escape_html(row.reference_no)}</a></td>
				<td>${frappe.utils.escape_html(row.subject || "")}</td>
				<td>${frappe.utils.escape_html(row.status || "")}</td>
				<td>${frappe.utils.escape_html(row.department || "")}</td>
			</tr>`)
				.appendTo(tbody)
				.find(".track-row-link")
				.on("click", (e) => {
					e.preventDefault();
					lookup_ref(row.name);
				});
		});
	}

	function lookup_ref(ref) {
		frappe.call({
			method: "masar_diwan.api.portal.get_tracking_detail",
			args: { ref, via: "barcode" },
			callback(r) {
				render_detail(r.message);
			},
		});
	}

	function render_detail(data) {
		if (!data || !data.found) {
			detail_wrapper.html(`<div class="alert alert-warning">${__("Reference not found")}</div>`);
			return;
		}
		if (data.restricted) {
			detail_wrapper.html(`
				<div class="correspondence-track-restricted">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20">
						<rect x="5" y="11" width="14" height="9" rx="1.5"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>
					</svg>
					<span>${__("Restricted content")} — ${__("You are not authorized to view this document")}</span>
				</div>
			`);
			return;
		}
		if (data.doctype === "Envelope") {
			render_envelope_detail(data.data);
			return;
		}
		const d = data.data;
		const attachments = (data.attachments || [])
			.map(
				(f) =>
					`<li><a href="/api/method/masar_diwan.api.portal.download_attachment?file_id=${encodeURIComponent(
						f.name
					)}" target="_blank">${frappe.utils.escape_html(f.file_name)}</a></li>`
			)
			.join("");
		const qr_html = d.qr_code
			? `<div style="flex:0 0 auto; text-align:center;"><img src="${frappe.utils.escape_html(d.qr_code)}" alt="${__("Tracking QR Code")}" style="width:110px; height:110px; object-fit:contain; border:1px solid var(--md-ink-100, #eff2f5); border-radius:9px;"></div>`
			: "";
		detail_wrapper.html(`
			<div class="card correspondence-track-card">
				<div class="correspondence-track-card__header">
					<a class="ref-code" href="/app/correspondence/${encodeURIComponent(d.name)}">${frappe.utils.escape_html(d.reference_no)}</a>
					${confidentiality_badge_html(d.confidentiality)}
				</div>
				<div class="card-body">
					${window.masarDiwanDesk.renderCorrespondenceStepper(d.status)}
					<div style="display:flex; gap:16px; flex-wrap:wrap-reverse; align-items:flex-start;">
						<div style="flex:1 1 220px;">
							<p><b>${__("Subject")}:</b> ${frappe.utils.escape_html(d.subject || "")}</p>
							<p><b>${__("Status")}:</b> ${frappe.utils.escape_html(__(d.status || ""))}</p>
							<p><b>${__("Department")}:</b> ${frappe.utils.escape_html(d.department || "")}</p>
						</div>
						${qr_html}
					</div>
					${attachments ? `<p><b>${__("Attachments")}:</b></p><ul>${attachments}</ul>` : ""}
				</div>
			</div>
		`);
	}

	function render_envelope_detail(e) {
		const rows = (e.documents || [])
			.map(
				(doc) => `<tr>
					<td><span class="ref-code">${frappe.utils.escape_html(doc.reference_no || doc.correspondence)}</span></td>
					<td>${frappe.utils.escape_html(doc.party_type || "-")}</td>
					<td>${frappe.utils.escape_html(doc.party || "-")}</td>
				</tr>`
			)
			.join("");
		detail_wrapper.html(`
			<div class="card correspondence-track-card">
				<div class="correspondence-track-card__header">
					<a class="ref-code" href="/app/envelope/${encodeURIComponent(e.name)}">${frappe.utils.escape_html(e.envelope_no)}</a>
				</div>
				<div class="card-body">
					<p><b>${__("Status")}:</b> ${frappe.utils.escape_html(__(e.status || ""))}</p>
					${e.linked_delivery_sheet ? `<p><b>${__("Linked Delivery Sheet")}:</b> <span class="ref-code">${frappe.utils.escape_html(e.linked_delivery_sheet)}</span></p>` : ""}
					<p><b>${__("Documents")} (${(e.documents || []).length}):</b></p>
					${
						rows
							? `<table class="table table-bordered"><thead><tr><th>${__("Reference No")}</th><th>${__("Party Type")}</th><th>${__("Party")}</th></tr></thead><tbody>${rows}</tbody></table>`
							: `<div class="text-muted">${__("No documents in this envelope.")}</div>`
					}
				</div>
			</div>
		`);
	}

	function confidentiality_badge_html(confidentiality) {
		if (!confidentiality || confidentiality === "Normal") return "";
		const cls = confidentiality === "Highly Confidential" ? "is-highly-confidential" : "is-confidential";
		return `<span class="correspondence-track-badge ${cls}">${frappe.utils.escape_html(__(confidentiality))}</span>`;
	}

	// The stepper itself is now rendered by the shared
	// window.masarDiwanDesk.renderCorrespondenceStepper() helper
	// (public/js/masar_diwan-desk.js, loaded app-wide) using the shared
	// .md-hstepper* CSS in masar_diwan-desk.css, instead of a copy of the
	// same 5-state array/markup kept in this file - see that helper's
	// header comment for the duplication this replaced.

	function inject_styles() {
		if ($("#correspondence-track-style").length) return;
		// Uses the shared --md-* identity tokens from masar_diwan-desk.css
		// (loaded app-wide via hooks.py) - presentational only.
		$(`<style id="correspondence-track-style">
			[data-page-route="correspondence-track"] .correspondence-track-card {
				border: 1px solid var(--md-ink-100, #eff2f5); border-radius: 15px; overflow: hidden;
				box-shadow: 0 1px 2px rgba(10,20,40,.04), 0 6px 20px -6px rgba(10,20,40,.10);
			}
			[data-page-route="correspondence-track"] .correspondence-track-card__header {
				background: var(--md-brand, #1a375b); color: #fff; padding: 14px 16px;
				display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
			}
			[data-page-route="correspondence-track"] .correspondence-track-card__header a.ref-code {
				color: #fff; font-size: 16px; font-weight: 600;
			}
			[data-page-route="correspondence-track"] .correspondence-track-badge {
				display: inline-flex; align-items: center; height: 20px; padding-inline: 8px;
				border-radius: 999px; font-size: 12px; font-weight: 500;
			}
			[data-page-route="correspondence-track"] .correspondence-track-badge.is-confidential {
				background: color-mix(in srgb, var(--md-warning, #d8790e) 20%, white); color: var(--md-warning, #d8790e);
			}
			[data-page-route="correspondence-track"] .correspondence-track-badge.is-highly-confidential {
				background: color-mix(in srgb, var(--md-danger, #ba2c3c) 16%, white); color: var(--md-danger, #ba2c3c);
			}
			[data-page-route="correspondence-track"] .correspondence-track-restricted {
				display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-radius: 9px;
				background: color-mix(in srgb, var(--md-danger, #ba2c3c) 8%, white); color: var(--md-danger, #ba2c3c);
			}
		</style>`).appendTo("head");
	}
};
