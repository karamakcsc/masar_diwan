// Simplified single-page submission form for "Correspondence Request" -
// lets any of the 4 roles that can already create one skip the generic
// multi-section Desk form. Creation still goes through the exact same
// server-side path (frappe.client.insert -> CorrespondenceRequest.before_insert(),
// frappe.model.workflow.apply_workflow -> the existing "Correspondence Request
// Workflow") - this page only builds a friendlier UI on top of it.
//
// Layout: two columns (main form cards on the right in RTL, a status/submitter
// sidebar on the left) per the approved v3 mockup - a pure visual restyle of
// the original single-column version, no backend/business logic changed here.
//
// Initial attachments have no dedicated DocType field (deliberate - see
// CLAUDE.md): they're staged client-side as plain File objects while no
// docname exists yet, then uploaded via the standard frappe.ui.FileUploader
// once the document has been created, exactly like any other doctype's
// "Attach" sidebar.

frappe.pages["correspondence-request-new"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("New Correspondence Request"),
		single_column: true,
	});

	new CorrespondenceRequestNew(page);
};

const CRN_STEPS = [
	{ key: "Draft", label: __("Draft") },
	{ key: "Pending Review", label: __("Pending Review") },
	{ key: "Under Review", label: __("Under Review") },
	{ key: "Approved", label: __("Approved") },
	{ key: "Approved & Numbered", label: __("Approved & Numbered") },
];

const CRN_STATUS_META = {
	Draft: { label: __("Draft"), color: "grey" },
	"Pending Review": { label: __("Pending Review"), color: "orange" },
	"Under Review": { label: __("Under Review"), color: "blue" },
	"Needs Revision": { label: __("Needs Revision"), color: "yellow" },
	Rejected: { label: __("Rejected"), color: "red" },
	Approved: { label: __("Approved"), color: "blue" },
	"Approved & Numbered": { label: __("Approved & Numbered"), color: "green" },
};

// Fallback shown only until the real Confidentiality Level list (which can
// vary per client/site - see Document Access Profile) is fetched over
// masar_diwan.api.requests.get_confidentiality_levels(). Never assume every
// site has exactly these 3 levels; this object is replaced wholesale by
// fetch_confidentiality_levels() as soon as that call returns.
const CRN_CONFIDENTIALITY_FALLBACK = {
	Normal: { label: __("Normal"), active_class: "btn-secondary" },
};

class CorrespondenceRequestNew {
	constructor(page) {
		this.page = page;
		this.saved_name = null;
		this.pending_files = [];
		this.request_type = null;
		this.priority = "Normal";
		this.confidentiality_meta = CRN_CONFIDENTIALITY_FALLBACK;
		this.confidentiality = "Normal";
		this.inject_styles();
		this.render_form();
	}

	// Builds the button-group HTML for whichever levels are currently known
	// (fallback on first paint, the real fetched list once it arrives).
	build_confidentiality_pills_html() {
		return Object.keys(this.confidentiality_meta)
			.map((key) => {
				const meta = this.confidentiality_meta[key];
				const is_active = this.confidentiality === key;
				const cls = is_active ? meta.active_class : "btn-outline-secondary";
				return `<button type="button" class="btn ${cls} crn-confidentiality-pill" aria-pressed="${is_active}" data-value="${frappe.utils.escape_html(key)}">${frappe.utils.escape_html(
					__(meta.label)
				)}</button>`;
			})
			.join("");
	}

	// Replaces the 3-hardcoded-levels assumption with whatever this site is
	// actually configured with (Document Access Profile / Confidentiality
	// Level are already N-level-capable server-side - see CLAUDE.md). The
	// two extremes keep the original grey/red convention; anything in
	// between gets the amber "confidential" treatment, generalizing the old
	// fixed 3-tier color scheme to any number of levels.
	fetch_confidentiality_levels($body) {
		frappe.call({
			method: "masar_diwan.api.requests.get_confidentiality_levels",
			callback: (r) => {
				const levels = r.message || [];
				if (!levels.length) return; // keep the fallback rather than showing an empty group
				const meta = {};
				levels.forEach((lvl, i) => {
					let active_class = "btn-warning";
					if (i === 0) active_class = "btn-secondary";
					else if (i === levels.length - 1) active_class = "btn-danger";
					meta[lvl.name] = { label: lvl.level_name || lvl.name, active_class };
				});
				this.confidentiality_meta = meta;
				if (!meta[this.confidentiality]) {
					this.confidentiality = levels[0].name;
				}
				$body.find("#crn-confidentiality-group").html(this.build_confidentiality_pills_html());
			},
		});
	}

	inject_styles() {
		if ($("#correspondence-request-new-style").length) return;
		// Colors/radii/shadows below reference the shared --md-* identity
		// tokens defined once in masar_diwan-desk.css (loaded app-wide via
		// hooks.py app_include_css) - this block is layout/structure only,
		// no business logic. Cards use --md-ink-50 background with a very
		// light --md-ink-100 border per the new visual identity; the dashed
		// dropzone and small elements (badges, file chips) intentionally use
		// the smaller --md-radius-sm, while nothing here needs the large
		// card radius since Bootstrap's own .card already gets that below.
		$(`<style id="correspondence-request-new-style">
			.correspondence-request-new-page .card {
				background: var(--md-ink-50); border: 1px solid var(--md-ink-100);
				border-radius: var(--md-radius-lg, 15px);
				box-shadow: 0 1px 2px rgba(10,20,40,.04), 0 6px 20px -6px rgba(10,20,40,.10);
			}
			.correspondence-request-new-page .btn-primary {
				background: var(--md-brand); border-color: var(--md-brand);
			}
			.correspondence-request-new-page .btn-primary:hover,
			.correspondence-request-new-page .btn-primary:focus {
				background: var(--md-brand-strong); border-color: var(--md-brand-strong);
			}
			.correspondence-request-new-page .btn-outline-primary {
				color: var(--md-brand); border-color: var(--md-brand);
			}
			.correspondence-request-new-page .btn-secondary,
			.correspondence-request-new-page .btn-outline-secondary.active {
				background: var(--md-ink-100); border-color: var(--md-ink-100); color: var(--md-ink-900);
			}
			.correspondence-request-new-page .btn-warning {
				background: var(--md-warning); border-color: var(--md-warning); color: #fff;
			}
			.correspondence-request-new-page .btn-danger {
				background: var(--md-danger); border-color: var(--md-danger); color: #fff;
			}
			.correspondence-request-new-page .crn-stepper-v { display: flex; flex-direction: column; }
			.correspondence-request-new-page .crn-step-v {
				display: flex; align-items: flex-start; gap: 10px; position: relative; padding-bottom: 22px;
			}
			.correspondence-request-new-page .crn-step-v:last-child { padding-bottom: 0; }
			.correspondence-request-new-page .crn-circle-v {
				width: 28px; height: 28px; min-width: 28px; border-radius: 50%; background: var(--md-ink-100);
				color: var(--md-ink-900); display: flex; align-items: center; justify-content: center;
				font-size: 12px; font-weight: 600; position: relative; z-index: 1;
			}
			.correspondence-request-new-page .crn-step-v:not(:last-child) .crn-circle-v:after {
				content: ""; position: absolute; top: 28px; inset-inline-start: 50%; transform: translateX(-50%);
				width: 2px; height: 22px; background: var(--md-ink-100);
			}
			.correspondence-request-new-page .crn-step-v.active .crn-circle-v { background: var(--md-brand); color: #fff; }
			.correspondence-request-new-page .crn-step-v.done .crn-circle-v { background: var(--md-success); color: #fff; }
			.correspondence-request-new-page .crn-step-text { padding-top: 3px; }
			.correspondence-request-new-page .crn-step-label { font-size: 13px; color: var(--md-ink-900); opacity: .55; }
			.correspondence-request-new-page .crn-step-v.active .crn-step-label,
			.correspondence-request-new-page .crn-step-v.done .crn-step-label { color: var(--md-ink-900); opacity: 1; font-weight: 600; }
			.correspondence-request-new-page .crn-avatar {
				width: 56px; height: 56px; border-radius: 50%; background: var(--md-brand); color: #fff;
				display: flex; align-items: center; justify-content: center; font-size: 22px;
				font-weight: 600; margin: 0 auto;
			}
			.correspondence-request-new-page .crn-type-btn {
				display: flex; flex-direction: column; align-items: center; justify-content: center;
				width: 100%; padding: 16px 8px; border-radius: var(--md-radius-sm, 9px); gap: 6px;
			}
			.correspondence-request-new-page .crn-type-btn svg { width: 22px; height: 22px; }
			.correspondence-request-new-page .crn-readonly-label { font-size: 12px; color: var(--md-ink-900); opacity: .55; margin-bottom: 2px; }
			.correspondence-request-new-page .crn-readonly-value { font-weight: 500; }
			.correspondence-request-new-page .crn-dropzone {
				border: 2px dashed var(--md-ink-100); border-radius: var(--md-radius-sm, 9px); padding: 25px; text-align: center;
				color: var(--md-ink-900); opacity: .6; cursor: pointer; margin-bottom: 10px;
				transition: border-color .15s ease, color .15s ease, background .15s ease;
			}
			.correspondence-request-new-page .crn-dropzone:hover {
				border-color: var(--md-brand); color: var(--md-brand); opacity: 1;
			}
			.correspondence-request-new-page .crn-dropzone.dragover {
				border-color: var(--md-brand); color: var(--md-brand); opacity: 1;
				background: color-mix(in srgb, var(--md-brand) 6%, white);
			}
			.correspondence-request-new-page .crn-file-card {
				display: flex; align-items: center; gap: 8px; border: 1px solid var(--md-ink-100); border-radius: var(--md-radius-sm, 9px);
				padding: 8px 10px; margin-bottom: 6px;
			}
			.correspondence-request-new-page .crn-file-icon {
				width: 32px; height: 32px; min-width: 32px; border-radius: var(--md-radius-sm, 9px); display: flex;
				align-items: center; justify-content: center; color: #fff;
			}
			.correspondence-request-new-page .crn-file-icon svg { color: #fff; }
			.correspondence-request-new-page .crn-file-icon.crn-file-pdf { background: var(--md-danger); }
			.correspondence-request-new-page .crn-file-icon.crn-file-image { background: var(--md-success); }
			.correspondence-request-new-page .crn-file-icon.crn-file-doc { background: var(--md-info); }
			.correspondence-request-new-page .crn-file-icon.crn-file-default { background: var(--md-ink-900); opacity: .55; }
			.correspondence-request-new-page .crn-file-meta { flex: 1; min-width: 0; }
			.correspondence-request-new-page .crn-file-name {
				font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
			}
			.correspondence-request-new-page .crn-file-size { font-size: 11px; color: var(--md-ink-900); opacity: .55; }
			.correspondence-request-new-page .crn-help-card { display: flex; gap: 8px; }
			.correspondence-request-new-page .crn-qr-disabled-wrap {
				position: relative; width: 120px; height: 120px; margin: 0 auto;
				filter: grayscale(1); opacity: 0.45;
			}
			.correspondence-request-new-page .crn-qr-disabled-wrap svg { width: 100%; height: 100%; }
			.correspondence-request-new-page .crn-qr-lock {
				position: absolute; top: 50%; inset-inline-start: 50%; transform: translate(-50%, -50%);
				width: 32px; height: 32px; border-radius: 50%; background: var(--md-brand-strong); color: #fff;
				display: flex; align-items: center; justify-content: center; opacity: 1; filter: none;
			}
			.correspondence-request-new-page .crn-qr-lock svg { width: 16px; height: 16px; }
			.correspondence-request-new-page .crn-success-icon {
				width: 64px; height: 64px; border-radius: 50%; background: var(--md-success); color: #fff;
				display: flex; align-items: center; justify-content: center; margin: 0 auto; font-size: 32px;
			}
		</style>`).appendTo("head");
	}

	format_file_size(bytes) {
		if (bytes == null) return "";
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	file_icon_meta(filename) {
		const ext = (filename.split(".").pop() || "").toLowerCase();
		if (ext === "pdf") return { cls: "crn-file-pdf" };
		if (["png", "jpg", "jpeg", "gif", "svg", "webp"].includes(ext)) return { cls: "crn-file-image" };
		if (["doc", "docx", "xls", "xlsx", "ppt", "pptx"].includes(ext)) return { cls: "crn-file-doc" };
		return { cls: "crn-file-default" };
	}

	// Purely decorative placeholder - a Correspondence Request has no QR
	// field and never will (see CLAUDE.md); this never encodes real data.
	// Fixed pattern (not random) so it looks the same on every render.
	render_fake_qr_svg() {
		const finder = (x, y) => `
			<rect x="${x}" y="${y}" width="21" height="21" fill="#36414c"/>
			<rect x="${x + 3}" y="${y + 3}" width="15" height="15" fill="#fff"/>
			<rect x="${x + 6}" y="${y + 6}" width="9" height="9" fill="#36414c"/>
		`;
		const modules = [
			[30, 5], [40, 5], [60, 5], [70, 5], [85, 5],
			[30, 15], [50, 15], [65, 15], [80, 15],
			[5, 30], [15, 30], [35, 30], [45, 30], [55, 30], [75, 30], [90, 30],
			[10, 40], [30, 40], [40, 40], [60, 40], [70, 40], [85, 40],
			[5, 55], [20, 55], [35, 55], [50, 55], [65, 55], [80, 55],
			[10, 65], [25, 65], [45, 65], [60, 65], [75, 65], [90, 65],
			[35, 75], [45, 75], [65, 75], [80, 75],
			[30, 85], [50, 85], [70, 85], [85, 85],
		];
		return `
			<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
				<rect width="100" height="100" fill="#fff"/>
				${finder(4, 4)}
				${finder(75, 4)}
				${finder(4, 75)}
				${modules.map(([x, y]) => `<rect x="${x}" y="${y}" width="8" height="8" fill="#36414c"/>`).join("")}
			</svg>
		`;
	}

	render_stepper_vertical(current_status) {
		const idx = Math.max(
			0,
			CRN_STEPS.findIndex((s) => s.key === current_status)
		);
		return `<div class="crn-stepper-v">${CRN_STEPS.map((s, i) => {
			let cls = "";
			let circle = i + 1;
			if (i < idx) {
				cls = "done";
				circle = "&#10003;";
			} else if (i === idx) {
				cls = "active";
			}
			return `<div class="crn-step-v ${cls}">
				<div class="crn-circle-v">${circle}</div>
				<div class="crn-step-text"><div class="crn-step-label">${s.label}</div></div>
			</div>`;
		}).join("")}</div>`;
	}

	render_form(prefill) {
		prefill = prefill || {};
		this.saved_name = prefill.name || null;
		this.request_type = prefill.request_type || null;
		this.priority = prefill.suggested_priority || "Normal";
		this.confidentiality = prefill.suggested_confidentiality || "Normal";
		this.pending_files = [];

		const status = prefill.status || "Draft";
		const status_meta = CRN_STATUS_META[status] || CRN_STATUS_META.Draft;

		const esc = frappe.utils.escape_html;
		const icon = frappe.utils.icon;
		const $body = $(this.page.body).empty();

		this.page.set_indicator(status_meta.label, status_meta.color);
		this.page.set_primary_action(__("Submit for Review"), () => this.save($body, "submit"));
		this.page.set_secondary_action(__("Save as Draft"), () => this.save($body, "draft"));

		$body.html(`
			<div class="correspondence-request-new-page" dir="${document.documentElement.dir || "ltr"}">
				<div class="crn-save-feedback" role="status" tabindex="-1"></div>
				${
					this.saved_name
						? `<div class="alert alert-info">${__("Draft saved with reference")}
							<a href="/app/correspondence-request/${encodeURIComponent(this.saved_name)}">
								${esc(this.saved_name)}
							</a></div>`
						: ""
				}
				<div class="row">
					<div class="col-lg-8">
						<div class="card mb-3"><div class="card-body">
							<h6 class="card-title">${__("Request details")}</h6>
							<label class="crn-readonly-label d-block mt-2">${__("Request Type")} <span class="text-danger">*</span></label>
							<div class="row">
								<div class="col-4">
									<button type="button" class="btn ${
										this.request_type === "Incoming" ? "btn-primary" : "btn-outline-primary"
									} crn-type-btn" aria-pressed="${this.request_type === "Incoming"}" data-value="Incoming">
										${icon("down-arrow", "lg")}
										<span>${__("Incoming")}</span>
									</button>
								</div>
								<div class="col-4">
									<button type="button" class="btn ${
										this.request_type === "Outgoing" ? "btn-primary" : "btn-outline-primary"
									} crn-type-btn" aria-pressed="${this.request_type === "Outgoing"}" data-value="Outgoing">
										${icon("up-arrow", "lg")}
										<span>${__("Outgoing")}</span>
									</button>
								</div>
								<div class="col-4">
									<button type="button" class="btn ${
										this.request_type === "Internal" ? "btn-primary" : "btn-outline-primary"
									} crn-type-btn" aria-pressed="${this.request_type === "Internal"}" data-value="Internal">
										${icon("home", "lg")}
										<span>${__("Internal")}</span>
									</button>
								</div>
							</div>

							<div class="row mt-3">
								<div class="col-sm-6">
									<div class="crn-readonly-label">${__("Submitted by")}</div>
									<div class="crn-readonly-value crn-submitter-line">...</div>
								</div>
								<div class="col-sm-6">
									<div class="crn-readonly-label">${__("Request Date")}</div>
									<div class="crn-readonly-value crn-date-line">...</div>
								</div>
							</div>

							<div class="form-group mt-3">
								<label for="crn-subject">${__("Subject")} <span class="text-danger">*</span></label>
								<input type="text" class="form-control" id="crn-subject" maxlength="140" aria-required="true" value="${esc(prefill.subject || "")}">
							</div>
							<div class="form-group mb-0">
								<label for="crn-party">${__("Party / Department")}</label>
								<input type="text" class="form-control" id="crn-party" value="${esc(prefill.party_or_department || "")}">
							</div>
						</div></div>

						<div class="card mb-3"><div class="card-body">
							<h6 class="card-title">${__("Classification")}</h6>
							<div class="row">
								<div class="col-sm-6 form-group">
									<label for="crn-category">${__("Category")}</label>
									<select class="form-control" id="crn-category"><option value="">-</option></select>
								</div>
								<div class="col-sm-6 form-group" id="crn-subcategory-group" style="display:none;">
									<label for="crn-subcategory">${__("Sub Category")}</label>
									<select class="form-control" id="crn-subcategory"><option value="">-</option></select>
								</div>
							</div>
							<div id="crn-dynamic-fields"></div>
						</div></div>

						<div class="card mb-3"><div class="card-body">
							<h6 class="card-title">${__("Draft Text")}</h6>
							<div id="crn-draft-text-wrapper"></div>
						</div></div>

						<div class="card mb-3"><div class="card-body">
							<h6 class="card-title">${__("Priority and confidentiality")}</h6>
							<div class="row">
								<div class="col-sm-6">
									<label class="d-block">${__("Priority")}</label>
									<div class="btn-group" role="group">
										<button type="button" class="btn ${
											this.priority === "Normal" ? "btn-primary" : "btn-outline-secondary"
										} crn-priority-pill" aria-pressed="${this.priority === "Normal"}" data-value="Normal">${__("Normal")}</button>
										<button type="button" class="btn ${
											this.priority === "Urgent" ? "btn-primary" : "btn-outline-secondary"
										} crn-priority-pill" aria-pressed="${this.priority === "Urgent"}" data-value="Urgent">${__("Urgent")}</button>
									</div>
								</div>
								<div class="col-sm-6">
									<label class="d-block">${__("Confidentiality")}</label>
									<div class="btn-group" id="crn-confidentiality-group" role="group">
										${this.build_confidentiality_pills_html()}
									</div>
								</div>
							</div>
						</div></div>

						<div class="card mb-3"><div class="card-body">
							<h6 class="card-title">${__("Attachments")}</h6>
							<div class="crn-dropzone" id="crn-dropzone" role="button" tabindex="0" aria-label="${__("Choose attachments")}">
								${__("Drop files here or choose files")}
								<input type="file" id="crn-file-input" aria-label="${__("Attachments")}" multiple style="display:none;">
							</div>
							<div id="crn-file-list"></div>
						</div></div>

						<div class="card mb-3"><div class="card-body">
							<h6 class="card-title">${__("Note to Registrar")}</h6>
							<textarea class="form-control" id="crn-note" aria-label="${__("Note to Registrar")}" rows="2">${esc(prefill.note_to_registrar || "")}</textarea>
						</div></div>
					</div>

					<div class="col-lg-4">
						<div class="card mb-3"><div class="card-body">
							<h6 class="card-title">${__("Request status")}</h6>
							${this.render_stepper_vertical(status)}
						</div></div>

						<div class="card mb-3"><div class="card-body text-center">
							<div class="crn-avatar mb-2">${esc((frappe.session.user_fullname || "?").charAt(0))}</div>
							<div class="font-weight-bold">${esc(frappe.session.user_fullname || frappe.session.user)}</div>
							<div class="text-muted small crn-submitter-dept">...</div>
						</div></div>

						<div class="card mb-3 bg-light border-0"><div class="card-body">
							<div class="crn-help-card">
								<div>${icon("solid-info", "sm")}</div>
								<div class="small text-muted">${__("The Diwan team will review your request and may ask for changes before registering it.")}</div>
							</div>
						</div></div>
					</div>
				</div>
			</div>
		`);

		this.draft_text_control = frappe.ui.form.make_control({
			parent: $body.find("#crn-draft-text-wrapper"),
			df: { fieldtype: "Text Editor", fieldname: "draft_text", label: __("Draft Text") },
			render_input: true,
			only_input: true,
		});
		this.draft_text_control.refresh();
		if (prefill.draft_text) {
			this.draft_text_control.set_value(prefill.draft_text);
		}

		this.bind_events($body);
		this.fetch_submitter_context($body);
		this.fetch_confidentiality_levels($body);
		// Carries any csf_ values from a just-saved draft (see save()'s own
		// render_form(Object.assign({}, fields, {...})) call) through to
		// fetch_dynamic_fields() below, once the category/sub-category
		// restore path re-renders the controls - render_form() itself has
		// no other place to stash them.
		this._prefill_dynamic_values = prefill;
		this.fetch_categories($body, prefill.correspondence_category, prefill.correspondence_sub_category);
	}

	// Category/sub-category + their dynamic fields (masar_diwan.install.
	// ensure_dynamic_fields()) - the standard Desk form's link_filters/
	// depends_on do this for free, but this page builds its own controls by
	// hand, so it needs the same three shared endpoints
	// (get_top_level_categories/get_sub_categories/get_dynamic_fields) and
	// the shared window.masarDiwanDynamicFields renderer instead of
	// re-implementing either.
	//
	// restoreCategory/restoreSubCategory: re-selecting these after a
	// Save-as-Draft round trip (render_form() re-runs with the just-saved
	// fields as prefill) was a real gap found live - without this, the
	// pickers and dynamic fields silently reset to empty the moment the
	// form re-rendered, even though the draft itself still had the right
	// values saved server-side.
	async fetch_categories($body, restoreCategory, restoreSubCategory) {
		this.category_loading = true;
		const $select = $body.find("#crn-category").prop("disabled", true);
		try {
			const r = await frappe.call({ method: "masar_diwan.api.requests.get_top_level_categories" });
			this.categories_meta = {};
			(r.message || []).forEach(cat => {
				this.categories_meta[cat.name] = cat;
				$select.append(new Option(cat.title, cat.name));
			});
			if (restoreCategory && this.categories_meta[restoreCategory]) $select.val(restoreCategory);
			await this.on_category_change($body, restoreSubCategory);
		} catch (error) {
			frappe.msgprint(__("Categories could not be loaded. Reload this page to try again."));
		} finally { $select.prop("disabled", false); }
	}

	async on_category_change($body, restoreSubCategory) {
		const sequence = this.category_sequence = (this.category_sequence || 0) + 1;
		this.category_loading = true;
		const category = $body.find("#crn-category").val();
		this.correspondence_category = category || null;
		this.correspondence_sub_category = restoreSubCategory || null;
		const isGroup = Boolean(this.categories_meta?.[category]?.is_group);
		const $subSelect = $body.find("#crn-subcategory").empty().append(new Option("-", ""));
		$body.find("#crn-subcategory-group").toggle(isGroup);
		$subSelect.prop("required", isGroup).prop("disabled", true);
		try {
			if (isGroup) {
				const r = await frappe.call({ method: "masar_diwan.api.requests.get_sub_categories", args: { correspondence_category: category } });
				if (sequence !== this.category_sequence) return;
				(r.message || []).forEach(sub => $subSelect.append(new Option(sub.title, sub.name)));
				if (restoreSubCategory) $subSelect.val(restoreSubCategory);
				this.correspondence_sub_category = $subSelect.val() || null;
			}
			await this.fetch_dynamic_fields($body, sequence);
		} catch (error) {
			if (sequence === this.category_sequence) frappe.msgprint(__("Category fields could not be loaded. Select the category again to retry."));
		} finally { if (sequence === this.category_sequence) $subSelect.prop("disabled", false); }
	}

	async fetch_dynamic_fields($body, sequence) {
		if (sequence === undefined) sequence = this.category_sequence = (this.category_sequence || 0) + 1;
		this.category_loading = true;
		const host = $body.find("#crn-dynamic-fields")[0];
		this._prefill_dynamic_values = Object.assign({}, this._prefill_dynamic_values, window.masarDiwanDynamicFields.collectValues(host));
		host.setAttribute("aria-busy", "true");
		try {
			const r = await frappe.call({ method: "masar_diwan.api.requests.get_dynamic_fields", args: {
				correspondence_category: this.correspondence_category,
				correspondence_sub_category: this.correspondence_sub_category,
			} });
			if (sequence !== this.category_sequence || !host.isConnected) return;
			Object.assign(this._prefill_dynamic_values, window.masarDiwanDynamicFields.collectValues(host));
			window.masarDiwanDynamicFields.render(host, r.message || [], this._prefill_dynamic_values);
			this.category_loading = false;
		} catch (error) {
			if (sequence === this.category_sequence) frappe.msgprint(__("Category fields could not be loaded. Select the category again to retry."));
		} finally { if (sequence === this.category_sequence) host.setAttribute("aria-busy", "false"); }
	}

	fetch_submitter_context($body) {
		frappe.call({
			method: "masar_diwan.api.requests.get_submitter_context",
			callback: (r) => {
				const data = r.message || {};
				const dept = data.department || "-";
				const date_str = data.date ? frappe.datetime.str_to_user(data.date) : "";
				$body.find(".crn-submitter-line").text(`${data.full_name || frappe.session.user} — ${dept}`);
				$body.find(".crn-date-line").text(date_str);
				$body.find(".crn-submitter-dept").text(dept);
			},
		});
	}

	bind_events($body) {
		$body.find(".crn-type-btn").on("click", (e) => {
			this.request_type = $(e.currentTarget).data("value");
			$body.find(".crn-type-btn").attr("aria-pressed", "false").removeClass("btn-primary").addClass("btn-outline-primary");
			$(e.currentTarget).attr("aria-pressed", "true").removeClass("btn-outline-primary").addClass("btn-primary");
		});

		$body.find(".crn-priority-pill").on("click", (e) => {
			this.priority = $(e.currentTarget).data("value");
			$body.find(".crn-priority-pill").attr("aria-pressed", "false").removeClass("btn-primary").addClass("btn-outline-secondary");
			$(e.currentTarget).attr("aria-pressed", "true").removeClass("btn-outline-secondary").addClass("btn-primary");
		});

		// Delegated (not bound directly to the .crn-confidentiality-pill
		// buttons themselves) because fetch_confidentiality_levels() replaces
		// #crn-confidentiality-group's innerHTML once the real level list
		// arrives - a direct .on("click") binding would be lost on that swap.
		$body.on("click", ".crn-confidentiality-pill", (e) => {
			this.confidentiality = $(e.currentTarget).data("value");
			$body.find(".crn-confidentiality-pill").each((_, el) => {
				const $el = $(el);
				const meta = this.confidentiality_meta[$el.data("value")];
				if (!meta) return;
				$el.attr("aria-pressed", "false").removeClass(`btn-outline-secondary ${meta.active_class}`).addClass("btn-outline-secondary");
			});
			const meta = this.confidentiality_meta[this.confidentiality];
			if (meta) {
				$(e.currentTarget).attr("aria-pressed", "true").removeClass("btn-outline-secondary").addClass(meta.active_class);
			}
		});

		$body.find("#crn-category").on("change", () => this.on_category_change($body));
		$body.find("#crn-subcategory").on("change", (e) => {
			this.correspondence_sub_category = $(e.currentTarget).val() || null;
			this.fetch_dynamic_fields($body);
		});

		const $dropzone = $body.find("#crn-dropzone");
		const $file_input = $body.find("#crn-file-input");
		$dropzone.on("click", (event) => {
			if (event.target !== $file_input[0]) $file_input[0].click();
		});
		$dropzone.on("keydown", event => {
			if (event.key === "Enter" || event.key === " ") {
				event.preventDefault();
				$file_input[0].click();
			}
		});
		$file_input.on("change", (e) => {
			this.add_files($body, e.target.files);
			e.target.value = "";
		});
		$dropzone.on("dragover", (e) => {
			e.preventDefault();
			$dropzone.addClass("dragover");
		});
		$dropzone.on("dragleave", () => $dropzone.removeClass("dragover"));
		$dropzone.on("drop", (e) => {
			e.preventDefault();
			$dropzone.removeClass("dragover");
			const dt = e.originalEvent.dataTransfer;
			if (dt && dt.files) this.add_files($body, dt.files);
		});

		this.render_file_list($body);
	}

	add_files($body, file_list) {
		Array.from(file_list).forEach((f) => this.pending_files.push(f));
		this.render_file_list($body);
	}

	render_file_list($body) {
		const esc = frappe.utils.escape_html;
		const $list = $body.find("#crn-file-list");
		$list.empty();
		this.pending_files.forEach((f, idx) => {
			const meta = this.file_icon_meta(f.name);
			$(`<div class="crn-file-card">
				<div class="crn-file-icon ${meta.cls}">${frappe.utils.icon("small-file", "xs")}</div>
				<div class="crn-file-meta">
					<div class="crn-file-name">${esc(f.name)}</div>
					<div class="crn-file-size">${this.format_file_size(f.size)}</div>
				</div>
				<button type="button" class="btn btn-link text-danger crn-remove-file" aria-label="${esc(__("Remove attachment") + ": " + f.name)}" data-idx="${idx}">&times;</button>
			</div>`).appendTo($list);
		});
		$list.find(".crn-remove-file").on("click", (e) => {
			e.preventDefault();
			const idx = $(e.currentTarget).data("idx");
			this.pending_files.splice(idx, 1);
			this.render_file_list($body);
		});
	}

	async upload_pending_files(docname) {
		const results = await Promise.all(this.pending_files.map(async file => {
			const body = new FormData();
			body.append("file", file);
			body.append("doctype", "Correspondence Request");
			body.append("docname", docname);
			body.append("is_private", "1");
			try {
				const response = await fetch("/api/method/upload_file", {
					method: "POST", headers: { "X-Frappe-CSRF-Token": frappe.csrf_token }, body,
				});
				if (!response.ok) return false;
				const result = await response.json();
				return Boolean(result.message && result.message.name);
			} catch (error) { return false; }
		}));
		this.pending_files = this.pending_files.filter((file, index) => !results[index]);
		if (this.pending_files.length) throw new Error("attachment-upload");
	}

	async save($body, action) {
		if (this.saving) return;
		if (this.category_loading) { frappe.msgprint(__("Wait for the category fields to finish loading before saving.")); return; }
		const subcategory = $body.find("#crn-subcategory")[0];
		if (subcategory.required && !subcategory.checkValidity()) { subcategory.reportValidity(); subcategory.focus(); return; }
		const subject = $body.find("#crn-subject").val().trim();
		if (!this.request_type || !subject) {
			frappe.msgprint({
				message: __("Select a request type and enter a subject to continue."),
				indicator: "orange",
			});
			return;
		}

		if (!window.masarDiwanDynamicFields.validate($body.find("#crn-dynamic-fields")[0])) return;
		this.saving = true;
		const fields = Object.assign(
			{
				request_type: this.request_type,
				subject: subject,
				party_or_department: $body.find("#crn-party").val().trim(),
				draft_text: this.draft_text_control.get_value() || "",
				suggested_priority: this.priority,
				suggested_confidentiality: this.confidentiality,
				note_to_registrar: $body.find("#crn-note").val().trim(),
				correspondence_category: this.correspondence_category || null,
				correspondence_sub_category: this.correspondence_sub_category || null,
			},
			window.masarDiwanDynamicFields.collectValues($body.find("#crn-dynamic-fields")[0])
		);

		frappe.dom.freeze(action === "submit" ? __("Submitting for review…") : __("Saving draft…"));

		try {
			let doc;
			if (this.saved_name) {
				doc = await frappe.xcall("frappe.client.set_value", {
					doctype: "Correspondence Request",
					name: this.saved_name,
					fieldname: fields,
				});
			} else {
				doc = await frappe.xcall("frappe.client.insert", {
					doc: Object.assign({ doctype: "Correspondence Request" }, fields),
				});
				this.saved_name = doc.name;
			}

			await this.upload_pending_files(doc.name);

			if (action === "submit") {
				doc = await frappe.xcall("frappe.model.workflow.apply_workflow", {
					doc: { doctype: "Correspondence Request", name: doc.name },
					action: "Submit",
				});
				frappe.dom.unfreeze();
				this.render_confirmation(doc);
			} else {
				frappe.dom.unfreeze();
				frappe.show_alert({ message: __("Saved as draft."), indicator: "green" });
				this.render_form(Object.assign({}, fields, { name: doc.name, status: doc.status }));
			}
		} catch (error) {
			this.render_file_list($body);
			$body.find(".crn-save-feedback").addClass("alert alert-danger").text(
				error.message === "attachment-upload"
					? __("Draft saved, but some attachments failed to upload. Retry to upload the remaining files before submitting.")
					: __("Could not complete this action. Your entered details are still available; please try again.")
			).trigger("focus");
		} finally {
			this.saving = false;
			frappe.dom.unfreeze();
		}
	}

	render_confirmation(doc) {
		const esc = frappe.utils.escape_html;
		const status_meta = CRN_STATUS_META[doc.status] || CRN_STATUS_META["Pending Review"];
		this.page.set_indicator(status_meta.label, status_meta.color);
		this.page.clear_actions();

		const $body = $(this.page.body).empty();
		$body.html(`
			<div class="correspondence-request-new-page" dir="${document.documentElement.dir || "ltr"}">
				<div class="crn-save-feedback" role="status" tabindex="-1"></div>
				<div class="row">
					<div class="col-lg-8">
						<div class="card"><div class="card-body text-center py-5">
							<div class="crn-success-icon">&#10003;</div>
							<h4 class="mt-3">${__("Request submitted for review")}</h4>
							<p class="text-muted">${__("Request reference:")} <strong>${esc(doc.name)}</strong></p>
							<div class="mt-4">
								<button type="button" class="btn btn-default" id="crn-view-request">${__("View Request")}</button>
								<button type="button" class="btn btn-primary" id="crn-new-request">${__("New Request")}</button>
							</div>
						</div></div>
					</div>
					<div class="col-lg-4">
						<div class="card mb-3"><div class="card-body">
							<h6 class="card-title">${__("Request status")}</h6>
							${this.render_stepper_vertical(doc.status)}
						</div></div>

						<div class="card mb-3"><div class="card-body text-center">
							<h6 class="card-title text-right">${__("Tracking QR Code")}</h6>
							<div class="crn-qr-disabled-wrap">
								${this.render_fake_qr_svg()}
								<div class="crn-qr-lock">${frappe.utils.icon("restriction", "xs")}</div>
							</div>
							<div class="text-muted small mt-2">${__("A tracking QR code becomes available after approval and official registration.")}</div>
						</div></div>

						<div class="card mb-3"><div class="card-body text-center">
							<div class="crn-avatar mb-2">${esc((frappe.session.user_fullname || "?").charAt(0))}</div>
							<div class="font-weight-bold">${esc(frappe.session.user_fullname || frappe.session.user)}</div>
						</div></div>
					</div>
				</div>
			</div>
		`);
		$body.find("#crn-view-request").on("click", () => {
			frappe.set_route("Form", "Correspondence Request", doc.name);
		});
		$body.find("#crn-new-request").on("click", () => {
			this.render_form();
		});
	}
}
