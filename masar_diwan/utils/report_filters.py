"""User-selected filters for correspondence reports; permission clauses stay separate."""

import frappe
from frappe import _
from frappe.utils import getdate


def correspondence_filters(filters, date_field):
	if date_field not in ("creation", "follow_up_date"):
		raise ValueError("Unsupported report date field")
	filters = frappe._dict(filters or {})
	clauses, values = [], {}
	for field in ("department", "current_owner", "correspondence_type"):
		if filters.get(field):
			clauses.append(f"and `tabCorrespondence`.`{field}` = %({field})s")
			values[field] = filters[field]
	for key in ("from_date", "to_date"):
		if filters.get(key):
			values[key] = getdate(filters[key])
	if values.get("from_date") and values.get("to_date") and values["from_date"] > values["to_date"]:
		frappe.throw(_("From Date must be on or before To Date."))
	if values.get("from_date"):
		clauses.append(f"and `tabCorrespondence`.`{date_field}` >= %(from_date)s")
	if values.get("to_date"):
		clauses.append(f"and `tabCorrespondence`.`{date_field}` < date_add(%(to_date)s, interval 1 day)")
	return "\n".join(clauses), values
