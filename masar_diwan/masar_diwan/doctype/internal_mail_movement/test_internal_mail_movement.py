# Copyright (c) 2026, Masar and Contributors
# See license.txt

"""Real integration tests for Internal Mail Movement's department-OR
permission scoping and its 3-state workflow. NOT executed against a live
bench in this session (no Frappe site/DB available here) - run with
`bench --site <site> run-tests --app masar_diwan --module
masar_diwan.masar_diwan.doctype.internal_mail_movement.test_internal_mail_movement`
before trusting it.

Deliberately NOT covered here: the Desk-UI "Workflow State" permission
error found via live browser testing (a Department Head / Diwan Officer /
Senior Management user could not open a brand-new Internal Mail Movement,
because every workflow state's `allow_edit` only listed "Correspondence
Employee" - fixed in internal_mail_movement_workflow.json by adding
allow_edit rows for the other 3 roles per state). That restriction is
enforced client-side by the Desk form's workflow integration against a
document that has never even reached the server yet - there is no
server-side permission check to assert against here, so a backend
IntegrationTestCase cannot exercise it at all (this mirrors the original
bug report itself: it was found via live browser testing precisely because
the existing API-only test harness could never have caught it). Confirming
the fix needs an actual browser session against a running Desk, the same
standing limitation CLAUDE.md already documents for every other visual/
UI-behavior claim in this app.
"""

import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests import IntegrationTestCase


def _make_department(name):
	if frappe.db.exists("Department", name):
		return name
	doc = frappe.get_doc({"doctype": "Department", "department_name": name})
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	return doc.name


def _make_user(email, roles, department=None):
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		)
		user.insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", email)
	existing_roles = {r.role for r in user.roles}
	for role in roles:
		if role not in existing_roles:
			user.append("roles", {"role": role})
	if user.roles:
		user.save(ignore_permissions=True)
	if department and not frappe.db.exists(
		"User Permission", {"user": email, "allow": "Department", "for_value": department}
	):
		frappe.get_doc(
			{"doctype": "User Permission", "user": email, "allow": "Department", "for_value": department}
		).insert(ignore_permissions=True)
	return email


class IntegrationTestInternalMailMovement(IntegrationTestCase):
	"""
	Integration tests for InternalMailMovement.
	Use this class for testing interactions between multiple components.
	"""

	def test_department_or_scoping(self):
		dept_from = _make_department("Test IMM From Dept")
		dept_to = _make_department("Test IMM To Dept")
		dept_other = _make_department("Test IMM Unrelated Dept")

		sender = _make_user("test.imm.sender@masar-diwan.local", ["Correspondence Employee"], dept_from)
		recipient = _make_user(
			"test.imm.recipient@masar-diwan.local", ["Correspondence Employee"], dept_to
		)
		outsider = _make_user(
			"test.imm.outsider@masar-diwan.local", ["Correspondence Employee"], dept_other
		)

		movement = frappe.get_doc(
			{
				"doctype": "Internal Mail Movement",
				"from_department": dept_from,
				"to_department": dept_to,
				"sender_name": "Test Sender",
				"content_description": "Department OR-scoping test",
			}
		).insert(ignore_permissions=True)

		try:
			frappe.set_user(sender)
			self.assertTrue(frappe.has_permission("Internal Mail Movement", "read", doc=movement.name))

			frappe.set_user(recipient)
			self.assertTrue(frappe.has_permission("Internal Mail Movement", "read", doc=movement.name))

			frappe.set_user(outsider)
			self.assertFalse(frappe.has_permission("Internal Mail Movement", "read", doc=movement.name))
		finally:
			frappe.set_user("Administrator")

	def test_confirm_receipt_requires_to_department_or_exempt_role(self):
		"""Regression test for the two real bugs documented in CLAUDE.md for
		this workflow: get_fullname() (not the unreliable
		session.user_fullname) backing sender_name/received_by, and the
		Confirm Receipt condition using non-permission-checked
		frappe.db.get_value (not frappe.db.get_list, which is
		permission-checked and would 403 a plain Correspondence Employee
		even on the unconditional Send transition).
		"""
		dept_from = _make_department("Test IMM Confirm From Dept")
		dept_to = _make_department("Test IMM Confirm To Dept")

		sender = _make_user(
			"test.imm.confirm.sender@masar-diwan.local", ["Correspondence Employee"], dept_from
		)
		recipient = _make_user(
			"test.imm.confirm.recipient@masar-diwan.local", ["Correspondence Employee"], dept_to
		)

		movement = frappe.get_doc(
			{
				"doctype": "Internal Mail Movement",
				"from_department": dept_from,
				"to_department": dept_to,
				"sender_name": "Test Sender",
				"content_description": "Confirm Receipt condition test",
			}
		).insert(ignore_permissions=True)

		try:
			frappe.set_user(sender)
			apply_workflow(movement, "Send")
			movement.reload()
			self.assertEqual(movement.status, "In Transit")

			# The sender (from_department, not to_department, no exempt role)
			# must not be able to confirm receipt on the other end.
			with self.assertRaises(Exception):
				apply_workflow(movement, "Confirm Receipt")
			movement.reload()
			self.assertEqual(movement.status, "In Transit")

			frappe.set_user(recipient)
			apply_workflow(movement, "Confirm Receipt")
			movement.reload()
			self.assertEqual(movement.status, "Received")
			self.assertTrue(movement.received_by)
			self.assertTrue(movement.received_on)
		finally:
			frappe.set_user("Administrator")
