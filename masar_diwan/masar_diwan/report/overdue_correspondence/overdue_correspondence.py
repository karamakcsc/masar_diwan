# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate

from masar_diwan.permissions import get_permission_query_conditions
from masar_diwan.utils.report_filters import correspondence_filters


def execute(filters=None):
	filter_clause, filter_values = correspondence_filters(filters, "follow_up_date")
	columns = [
		{"label": _("Reference No"), "fieldname": "name", "fieldtype": "Link", "options": "Correspondence", "width": 130},
		{"label": _("Subject"), "fieldname": "subject", "fieldtype": "Data", "width": 220},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150},
		{"label": _("Current Owner"), "fieldname": "current_owner", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": _("Follow-up Date"), "fieldname": "follow_up_date", "fieldtype": "Date", "width": 110},
		{"label": _("Days Overdue"), "fieldname": "days_overdue", "fieldtype": "Int", "width": 100},
	]

	# This report's role list (Correspondence Employee/Department Head/Diwan
	# Officer/Senior Management) is exactly the set that's department- and
	# confidentiality-scoped everywhere else in the app (list views, /track,
	# the portal) - a raw frappe.db.sql with no filter would let a plain
	# Correspondence Employee see every department's (including Highly
	# Confidential) overdue items here, bypassing permissions.py entirely.
	# Reusing the same conditions builder every other path already relies on,
	# not a separate ad-hoc rule that could drift from it.
	conditions = get_permission_query_conditions()
	permission_clause = f"and ({conditions})" if conditions else ""

	data = frappe.db.sql(
		f"""
		select
			name, subject, status, department, current_owner, follow_up_date,
			datediff(%(today)s, follow_up_date) as days_overdue
		from `tabCorrespondence`
		where follow_up_date is not null
			and follow_up_date < %(today)s
			and status not in ('Completed', 'Archived')
			{permission_clause}
			{filter_clause}
		order by follow_up_date asc
		""",
		{"today": nowdate(), **filter_values},
		as_dict=True,
	)

	summary = [
		{"label": _("Overdue Items"), "value": len(data), "datatype": "Int", "indicator": "Red"},
	]

	return columns, data, None, None, summary
