"""Read-only helper backing the "New Correspondence Request" Desk Page.

Only exposes what the page's informational banner needs to display before a
`Correspondence Request` exists yet (full name / department / today's date).
The actual document creation and Draft -> Pending Review transition are done
directly from the page's JS via the standard `frappe.client.insert` and
`frappe.model.workflow.apply_workflow` whitelisted methods, reusing
`CorrespondenceRequest.before_insert()` and the existing
`Correspondence Request Workflow` as-is - nothing here duplicates that logic.
"""

import frappe

from masar_diwan.permissions import get_user_departments


@frappe.whitelist()
def get_submitter_context():
	user = frappe.session.user
	departments = get_user_departments(user)
	return {
		"full_name": frappe.utils.get_fullname(user),
		"department": next(iter(departments), None),
		"date": frappe.utils.today(),
	}
