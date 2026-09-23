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
			// Data, Link - a plain text input; an invalid Link value is
			// still rejected server-side by Frappe's own standard
			// _validate_links() check on save, same as any other Link field.
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

		wrapper.appendChild(input);
		return wrapper;
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
