# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate


def execute(filters=None):
	columns = [
		{"label": _("Reference No"), "fieldname": "name", "fieldtype": "Link", "options": "Correspondence", "width": 130},
		{"label": _("Subject"), "fieldname": "subject", "fieldtype": "Data", "width": 220},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": _("Current Owner"), "fieldname": "current_owner", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": _("Follow-up Date"), "fieldname": "follow_up_date", "fieldtype": "Date", "width": 110},
		{"label": _("Days Overdue"), "fieldname": "days_overdue", "fieldtype": "Int", "width": 100},
	]

	data = frappe.db.sql(
		"""
		select
			name, subject, status, department, current_owner, follow_up_date,
			datediff(%(today)s, follow_up_date) as days_overdue
		from `tabCorrespondence`
		where follow_up_date is not null
			and follow_up_date < %(today)s
			and status not in ('Completed', 'Archived')
		order by follow_up_date asc
		""",
		{"today": nowdate()},
		as_dict=True,
	)

	summary = [
		{"label": _("Overdue Items"), "value": len(data), "datatype": "Int", "indicator": "Red"},
	]

	return columns, data, None, None, summary
