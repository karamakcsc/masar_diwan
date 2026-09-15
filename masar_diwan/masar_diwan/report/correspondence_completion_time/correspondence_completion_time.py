# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = [
		{"label": _("Reference No"), "fieldname": "name", "fieldtype": "Link", "options": "Correspondence", "width": 130},
		{"label": _("Subject"), "fieldname": "subject", "fieldtype": "Data", "width": 220},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": _("Created On"), "fieldname": "creation", "fieldtype": "Datetime", "width": 160},
		{"label": _("Completed On"), "fieldname": "completed_on", "fieldtype": "Datetime", "width": 160},
		{"label": _("Days to Complete"), "fieldname": "days_to_complete", "fieldtype": "Float", "width": 130},
	]

	data = frappe.db.sql(
		"""
		select
			c.name, c.subject, c.department, c.creation,
			min(tl.date) as completed_on,
			datediff(min(tl.date), c.creation) as days_to_complete
		from `tabCorrespondence` c
		inner join `tabCorrespondence Transfer Log` tl
			on tl.parent = c.name and tl.parenttype = 'Correspondence'
		where tl.note like %(pattern)s
		group by c.name
		order by c.creation desc
		""",
		{"pattern": "%to Completed%"},
		as_dict=True,
	)

	avg_days = sum(d.days_to_complete or 0 for d in data) / len(data) if data else 0

	summary = [
		{"label": _("Completed Items"), "value": len(data), "datatype": "Int"},
		{"label": _("Average Days to Complete"), "value": round(avg_days, 1), "datatype": "Float", "indicator": "Blue"},
	]

	return columns, data, None, None, summary
