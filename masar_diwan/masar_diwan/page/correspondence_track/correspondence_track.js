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
				<td><a href="#" class="track-row-link">${frappe.utils.escape_html(row.reference_no)}</a></td>
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
			detail_wrapper.html(
				`<div class="alert alert-danger">•• ${__("Restricted content")} •• ${__(
					"You are not authorized to view this correspondence"
				)}</div>`
			);
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
		detail_wrapper.html(`
			<div class="card"><div class="card-body">
				<h5><a href="/app/correspondence/${encodeURIComponent(d.name)}">${frappe.utils.escape_html(d.reference_no)}</a></h5>
				<p><b>${__("Subject")}:</b> ${frappe.utils.escape_html(d.subject || "")}</p>
				<p><b>${__("Status")}:</b> ${frappe.utils.escape_html(d.status || "")}</p>
				<p><b>${__("Department")}:</b> ${frappe.utils.escape_html(d.department || "")}</p>
				${attachments ? `<p><b>${__("Attachments")}:</b></p><ul>${attachments}</ul>` : ""}
			</div></div>
		`);
	}
};
