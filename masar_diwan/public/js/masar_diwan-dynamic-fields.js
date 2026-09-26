// Shared, dependency-free renderer for the per-category dynamic-field engine
// (masar_diwan.install.ensure_dynamic_fields() / Correspondence Category's own
// dynamic_fields child table). Deliberately plain DOM, not
// frappe.ui.form.make_control() - the two callers that need this
// (correspondence_request_new.js, a Desk Page, and www/diwan/submit, a plain
// website page) don't share a common Frappe widget bundle, only this one
// small file, loaded by both (see hooks.py's app_include_js and
// diwan_shell.html's own <script> tag).
(function () {
	var controlSequence = 0;
	function buildControl(field, currentValue) {
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
			input.appendChild(new Option(__("Select an option"), ""));
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

		input.id = "dyn-field-" + field.fieldname_slug + "-" + (++controlSequence);
		label.htmlFor = input.id;
		input.className = "md-dynamic-control";
		input.dataset.fieldname = fieldname;
		input.dataset.fieldtype = field.fieldtype;
		if (field.reqd) input.required = true;
		input.style.width = field.fieldtype === "Check" ? "auto" : "100%";
		input.style.boxSizing = "border-box";
		input.style.padding = "6px 8px";

		if (currentValue !== undefined && currentValue !== null) {
			if (field.fieldtype === "Check") {
				input.checked = !!(currentValue === 1 || currentValue === "1" || currentValue === true);
			} else {
				input.value = currentValue;
			}
		}

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
		const box = document.createElement("div");
		box.className = "md-link-picker";
		const menu = document.createElement("div");
		menu.className = "md-link-picker__menu";
		menu.id = input.id + "-options";
		menu.setAttribute("role", "listbox");
		menu.setAttribute("aria-label", field.label);
		menu.hidden = true;
		const message = document.createElement("div");
		message.className = "md-link-picker__message";
		message.setAttribute("role", "status");
		message.id = input.id + "-message";
		input.autocomplete = "off";
		input.setAttribute("role", "combobox");
		input.setAttribute("aria-autocomplete", "list");
		input.setAttribute("aria-controls", menu.id);
		input.setAttribute("aria-describedby", message.id);
		input.setAttribute("aria-expanded", "false");
		box.append(input, menu, message);
		let timer, sequence = 0, active = -1, options = [];
		function close() {
			menu.hidden = true;
			input.setAttribute("aria-expanded", "false");
			input.removeAttribute("aria-activedescendant");
			active = -1;
		}
		function choose(index) {
			if (!options[index]) return;
			input.value = options[index].value;
			sequence++;
			clearTimeout(timer);
			message.textContent = "";
			close();
			input.dispatchEvent(new Event("change", { bubbles: true }));
		}
		function highlight(index) {
			active = index;
			Array.from(menu.children).forEach((item, i) => item.setAttribute("aria-selected", String(i === index)));
			if (menu.children[index]) {
				input.setAttribute("aria-activedescendant", menu.children[index].id);
				menu.children[index].scrollIntoView({ block: "nearest" });
			}
		}
		async function search() {
			const request = ++sequence;
			message.textContent = __("Searching…");
			try {
				const response = await fetch("/api/method/frappe.desk.search.search_link?" + new URLSearchParams({ doctype: field.options, txt: input.value }), {
					headers: { "X-Frappe-CSRF-Token": frappe.csrf_token },
				});
				if (request !== sequence || !input.isConnected) return;
				if (!response.ok) {
					close();
					message.textContent = response.status === 403 ? __("You don't have access to search this.") : __("Search could not be completed. Please try again.");
					return;
				}
				const data = await response.json();
				if (request !== sequence || !input.isConnected) return;
				options = data.message || [];
				menu.replaceChildren();
				active = -1;
				options.forEach((option, index) => {
					const item = document.createElement("div");
					item.id = menu.id + "-" + index;
					item.setAttribute("role", "option");
					item.setAttribute("aria-selected", "false");
					item.textContent = option.description ? option.value + " — " + option.description : option.value;
					item.addEventListener("mousedown", event => event.preventDefault());
					item.addEventListener("click", () => choose(index));
					item.addEventListener("mouseenter", () => highlight(index));
					menu.appendChild(item);
				});
				menu.hidden = !options.length;
				input.setAttribute("aria-expanded", String(Boolean(options.length)));
				message.textContent = options.length ? "" : __("No matching options.");
			} catch (error) {
				if (request === sequence) { close(); message.textContent = __("Search could not be completed. Please try again."); }
			}
		}
		input.addEventListener("input", () => {
			sequence++;
			clearTimeout(timer);
			close();
			timer = setTimeout(search, 250);
		});
		input.addEventListener("focus", search);
		input.addEventListener("blur", () => { sequence++; clearTimeout(timer); close(); message.textContent = ""; });
		input.addEventListener("keydown", event => {
			if (event.key === "Escape") { sequence++; clearTimeout(timer); close(); }
			if (["ArrowDown", "ArrowUp"].includes(event.key)) {
				event.preventDefault();
				if (menu.hidden) { search(); return; }
				const next = event.key === "ArrowDown" ? (active + 1) % options.length : (active <= 0 ? options.length - 1 : active - 1);
				highlight(next);
			}
			if (event.key === "Enter" && !menu.hidden && active >= 0) { event.preventDefault(); choose(active); }
		});
		return box;
	}

	function render(containerEl, fields, currentValues) {
		currentValues = Object.assign({}, collectValues(containerEl), currentValues || {});
		containerEl.innerHTML = "";
		(fields || []).forEach(function (field) {
			var value = currentValues ? currentValues["csf_" + field.fieldname_slug] : undefined;
			containerEl.appendChild(buildControl(field, value));
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

	function validate(containerEl) {
		const invalid = Array.from(containerEl.querySelectorAll("[data-fieldname]")).find(input => !input.checkValidity());
		if (invalid) { invalid.reportValidity(); invalid.focus(); return false; }
		return true;
	}

	window.masarDiwanDynamicFields = { render: render, collectValues: collectValues, validate: validate };
})();
