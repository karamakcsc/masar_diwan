# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from masar_diwan.permissions import get_permission_query_conditions
from masar_diwan.utils.report_filters import correspondence_filters


def execute(filters=None):
	filter_clause, filter_values = correspondence_filters(filters, "creation")
	columns = [
		{"label": _("Reference No"), "fieldname": "name", "fieldtype": "Link", "options": "Correspondence", "width": 130},
		{"label": _("Subject"), "fieldname": "subject", "fieldtype": "Data", "width": 220},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": _("Created On"), "fieldname": "creation", "fieldtype": "Datetime", "width": 160},
		{"label": _("Completed On"), "fieldname": "completed_on", "fieldtype": "Datetime", "width": 160},
		{"label": _("Days to Complete"), "fieldname": "days_to_complete", "fieldtype": "Float", "width": 130},
	]

	# Same gap and same fix as overdue_correspondence.py: this report's roles
	# (Department Head/Diwan Officer/Senior Management) are department- and
	# confidentiality-scoped everywhere else - reuse permissions.py's own
	# conditions builder rather than leaving this raw SQL unfiltered.
	#
	# The query below deliberately does NOT alias `tabCorrespondence` (unlike
	# its previous `c` alias) - generic_get_permission_query_conditions()
	# hardcodes the literal, unaliased table name for its authorized-viewer
	# EXISTS subquery correlation (`` `tabCorrespondence`.name ``), confirmed
	# live: aliasing it as `c` here raised a real
	# `Unknown column 'tabCorrespondence.name'` MySQL error the moment a
	# confidentiality-tiered condition was actually exercised, not just a
	# theoretical concern.
	conditions = get_permission_query_conditions()
	permission_clause = f"and ({conditions})" if conditions else ""

	data = frappe.db.sql(
		f"""
		select
			`tabCorrespondence`.name, `tabCorrespondence`.subject, `tabCorrespondence`.department,
			`tabCorrespondence`.creation,
			min(tl.date) as completed_on,
			datediff(min(tl.date), `tabCorrespondence`.creation) as days_to_complete
		from `tabCorrespondence`
		inner join `tabCorrespondence Transfer Log` tl
			on tl.parent = `tabCorrespondence`.name and tl.parenttype = 'Correspondence'
		where tl.note like %(pattern)s
			{permission_clause}
			{filter_clause}
		group by `tabCorrespondence`.name
		order by `tabCorrespondence`.creation desc
		""",
		{"pattern": "%to Completed%", **filter_values},
		as_dict=True,
	)

	avg_days = sum(d.days_to_complete or 0 for d in data) / len(data) if data else 0

	summary = [
		{"label": _("Completed Items"), "value": len(data), "datatype": "Int"},
		{"label": _("Average Days to Complete"), "value": round(avg_days, 1), "datatype": "Float", "indicator": "Blue"},
	]

	return columns, data, None, None, summary
