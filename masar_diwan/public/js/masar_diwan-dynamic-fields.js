// Shared, dependency-free renderer for the per-category dynamic-field engine
// (masar_diwan.install.ensure_dynamic_fields() / Correspondence Category's own
// dynamic_fields child table). Deliberately plain DOM, not
// frappe.ui.form.make_control() - the two callers that need this
// (correspondence_request_new.js, a Desk Page, and www/diwan/submit, a plain
// website page) don't share a common Frappe widget bundle, only this one
// small file, loaded by both (see hooks.py's app_include_js and
// diwan_shell.html's own <script> tag).
(function () {
	function buildControl(field) {
		var wrapper = document.createElement("div");
		wrapper.className = "masar-dyn-field";
		wrapper.style.marginBottom = "10px";

		var label = document.createElement("label");
		label.textContent = field.label + (field.reqd ? " *" : "");
		label.style.display = "block";
		label.style.fontWeight = "600";
		label.style.marginBottom = "4px";
		wrapper.appendChild(label);

		var input;
		var fieldname = "csf_" + field.fieldname_slug;

		if (field.fieldtype === "Select") {
			input = document.createElement("select");
			(field.options || "").split("\n").filter(Boolean).forEach(function (opt) {
				var o = document.createElement("option");
				o.value = opt;
				o.textContent = opt;
				input.appendChild(o);
			});
		} else if (field.fieldtype === "Check") {
			input = document.createElement("input");
			input.type = "checkbox";
		} else if (field.fieldtype === "Date") {
			input = document.createElement("input");
			input.type = "date";
		} else if (field.fieldtype === "Int" || field.fieldtype === "Currency") {
			input = document.createElement("input");
			input.type = "number";
			if (field.fieldtype === "Currency") input.step = "any";
		} else {
			// Data - a plain text input. Link is handled separately below
			// (needs a real search/pick UI, not a bare text box - a portal
			// user has no way to guess a valid docname otherwise).
			input = document.createElement("input");
			input.type = "text";
		}

		input.id = "dyn-field-" + field.fieldname_slug;
		input.dataset.fieldname = fieldname;
		input.dataset.fieldtype = field.fieldtype;
		if (field.reqd) input.required = true;
		input.style.width = "100%";
		input.style.boxSizing = "border-box";
		input.style.padding = "6px 8px";

		if (field.fieldtype === "Link") {
			wrapper.appendChild(buildLinkAutocomplete(field, input));
		} else {
			wrapper.appendChild(input);
		}
		return wrapper;
	}

	// A real search-as-you-type picker for Link fields, using the same
	// frappe.desk.search.search_link endpoint Frappe's own Desk Link
	// control calls - respects normal read permissions (a plain text box
	// left a portal user with no way to find a valid value at all, and an
	// invalid one was only ever caught server-side, after the fact, by
	// Frappe's standard _validate_links() on save).
	function buildLinkAutocomplete(field, input) {
		var box = document.createElement("div");
		box.style.position = "relative";
		input.autocomplete = "off";
		box.appendChild(input);

		var menu = document.createElement("div");
		menu.style.cssText =
			"position:absolute;top:100%;left:0;right:0;background:#fff;border:1px solid #d1d8dd;" +
			"border-radius:4px;max-height:200px;overflow-y:auto;z-index:100;display:none;" +
			"box-shadow:0 2px 6px rgba(0,0,0,.12);";
		box.appendChild(menu);

		var debounceTimer;
		function renderMenu(items) {
			menu.innerHTML = "";
			items.forEach(function (item) {
				var el = document.createElement("div");
				el.textContent = item.label;
				el.style.cssText = "padding:6px 8px;cursor:pointer;color:" + (item.muted ? "#8d99a6" : "inherit") + ";";
				if (item.value) {
					el.addEventListener("mouseenter", function () {
						el.style.background = "#f4f5f6";
					});
					el.addEventListener("mouseleave", function () {
						el.style.background = "";
					});
					el.addEventListener("mousedown", function (e) {
						e.preventDefault();
						input.value = item.value;
						menu.style.display = "none";
					});
				}
				menu.appendChild(el);
			});
			menu.style.display = items.length ? "block" : "none";
		}

		function search(txt) {
			// Deliberately a raw fetch(), not frappe.call() - search_link
			// enforces normal read permission on the target doctype, and a
			// portal (Website User) session genuinely lacks it for most
			// ERPNext-internal doctypes (confirmed live: a real 403/
			// PermissionError, not just an empty result, searching Sales
			// Invoice as test.portal). frappe.call's own response handling
			// pops a default error dialog for that; fetch() lets this stay
			// a quiet, in-place "no matches" instead of an intrusive popup
			// for something the user can't do anything about anyway.
			fetch(
				"/api/method/frappe.desk.search.search_link?" +
					new URLSearchParams({ doctype: field.options, txt: txt || "" }),
				{ headers: { "X-Frappe-CSRF-Token": frappe.csrf_token } }
			)
				.then(function (resp) {
					if (!resp.ok) {
						renderMenu([{ label: __("You don't have access to search this."), muted: true }]);
						return null;
					}
					return resp.json();
				})
				.then(function (data) {
					if (!data) return;
					var results = data.message || [];
					if (!results.length) {
						menu.style.display = "none";
						return;
					}
					renderMenu(
						results.map(function (res) {
							return { value: res.value, label: res.description ? res.value + " — " + res.description : res.value };
						})
					);
				})
				.catch(function () {
					menu.style.display = "none";
				});
		}

		input.addEventListener("input", function () {
			clearTimeout(debounceTimer);
			var txt = input.value;
			debounceTimer = setTimeout(function () {
				search(txt);
			}, 300);
		});
		input.addEventListener("focus", function () {
			search(input.value);
		});
		input.addEventListener("blur", function () {
			setTimeout(function () {
				menu.style.display = "none";
			}, 150);
		});

		return box;
	}

	function render(containerEl, fields) {
		containerEl.innerHTML = "";
		(fields || []).forEach(function (field) {
			containerEl.appendChild(buildControl(field));
		});
	}

	function collectValues(containerEl) {
		var values = {};
		containerEl.querySelectorAll("[data-fieldname]").forEach(function (input) {
			var fieldname = input.dataset.fieldname;
			values[fieldname] = input.dataset.fieldtype === "Check" ? (input.checked ? 1 : 0) : input.value;
		});
		return values;
	}

	window.masarDiwanDynamicFields = { render: render, collectValues: collectValues };
})();
