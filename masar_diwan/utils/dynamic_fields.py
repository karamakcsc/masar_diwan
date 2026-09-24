"""Shared helpers for the per-category dynamic-field engine
(masar_diwan.install.ensure_dynamic_fields()). Every caller that needs to
know "which dynamic fields apply to this Correspondence Request/Correspondence,
and what are they" - server-side validation, the copy-on-approve step, the
portal's own creation and read-only detail pages - goes through the same
"effective category" rule and the same active-row lookup here, instead of
each re-deriving it independently.
"""

import frappe
from frappe import _


def get_effective_category(doc):
	"""The category whose dynamic_fields actually apply: the chosen
	sub-category if there is one, else the top-level category itself when
	it has no children (a leaf category used directly, no sub-category
	ever needed)."""
	return doc.get("correspondence_sub_category") or doc.get("correspondence_category")


def get_active_dynamic_field_rows(effective_category):
	if not effective_category or not frappe.db.exists("Correspondence Category", effective_category):
		return []
	category = frappe.get_cached_doc("Correspondence Category", effective_category)
	rows = [r for r in category.dynamic_fields if r.is_active]
	rows.sort(key=lambda r: (r.sort_order or 0, r.idx or 0))
	return rows


def get_dynamic_field_values_for_display(doc):
	"""[{label, value, fieldtype}] for a read-only detail view - only
	fields that actually have a value, formatted for display (Check as
	Yes/No, Date in the user's own date format) rather than raw stored
	values."""
	rows = get_active_dynamic_field_rows(get_effective_category(doc))
	result = []
	for row in rows:
		value = doc.get(f"csf_{row.fieldname_slug}")
		if value in (None, ""):
			continue
		if row.fieldtype == "Check":
			display_value = _("Yes") if cint_truthy(value) else _("No")
		elif row.fieldtype == "Date" and value:
			display_value = frappe.utils.format_date(value)
		else:
			display_value = value
		result.append({"label": row.label, "value": display_value, "fieldtype": row.fieldtype})
	return result


def cint_truthy(value):
	try:
		return int(value) != 0
	except (TypeError, ValueError):
		return bool(value)
