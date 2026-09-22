# Copyright (c) 2026, Masar and Contributors
# See license.txt

"""Real integration test coverage for the two most fragile, most-relied-on
pieces of custom logic behind Correspondence: the generic permission engine
(permissions.py) and the reference-numbering prefix-sync fix (numbering.py).

Written from a fresh audit of the app; NOT executed against a live bench in
this session (this sandbox has no Frappe site/DB to run against) - run with
`bench --site <site> run-tests --app masar_diwan --module
masar_diwan.masar_diwan.doctype.correspondence.test_correspondence` before
trusting it, and treat a failure as a real signal rather than assuming the
test itself is wrong.

Test fixtures (Department, Correspondence Type, User) are created directly
in each test rather than relying on Frappe's test_records.json mechanism -
none existed for this app before this file, and self-contained tests match
the disposable-script verification pattern this project has used throughout
(see CLAUDE.md "How to verify this still works").
"""

import frappe
from frappe.tests import IntegrationTestCase


def _make_department(name):
	"""Creates a minimal Department record regardless of which Department
	provider is active on this site (ERPNext's real Department, or
	masar_diwan's own custom=1 fallback - see install.py::ensure_department_doctype).
	ignore_mandatory=True sidesteps any ERPNext-only mandatory field (e.g. a
	possible `company` requirement) this test has no business asserting on.
	"""
	if frappe.db.exists("Department", name):
		return name
	doc = frappe.get_doc({"doctype": "Department", "department_name": name})
	doc.insert(ignore_permissions=True, ignore_mandatory=True)
	return doc.name


def _make_correspondence_type(title, prefix):
	name = f"Test {title}"
	if frappe.db.exists("Correspondence Type", name):
		return name
	doc = frappe.get_doc(
		{"doctype": "Correspondence Type", "title": name, "prefix": prefix}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _make_user(email, roles, department=None):
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
			}
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
	if department:
		if not frappe.db.exists(
			"User Permission", {"user": email, "allow": "Department", "for_value": department}
		):
			frappe.get_doc(
				{
					"doctype": "User Permission",
					"user": email,
					"allow": "Department",
					"for_value": department,
				}
			).insert(ignore_permissions=True)
	return email


class IntegrationTestCorrespondence(IntegrationTestCase):
	"""
	Integration tests for Correspondence.
	Use this class for testing interactions between multiple components.
	"""

	def test_numbering_prefix_drift_is_corrected_on_every_call(self):
		"""Regression test for the documented numbering.py fix: editing a
		Correspondence Type's prefix after its first-ever reference number
		must be reflected on the very next number issued, not silently
		ignored because the Correspondence Numbering Rule row still has the
		old prefix cached.
		"""
		ctype = _make_correspondence_type("Prefix Drift", "TPD")

		first = frappe.get_doc(
			{
				"doctype": "Correspondence",
				"correspondence_type": ctype,
				"subject": "First reference under old prefix",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(first.name.startswith("TPD-"))

		frappe.db.set_value("Correspondence Type", ctype, "prefix", "TPD2")

		second = frappe.get_doc(
			{
				"doctype": "Correspondence",
				"correspondence_type": ctype,
				"subject": "Second reference, should use the new prefix",
			}
		).insert(ignore_permissions=True)
		self.assertTrue(
			second.name.startswith("TPD2-"),
			f"expected the new prefix to be picked up immediately, got {second.name}",
		)

	def test_department_scoping_blocks_other_department(self):
		"""Department scoping (permissions.py::generic_has_permission) - a
		user in Department A must not be able to read a Correspondence
		scoped to Department B, and it must not appear in their list either.
		"""
		dept_a = _make_department("Test Dept A - Perm Audit")
		dept_b = _make_department("Test Dept B - Perm Audit")
		ctype = _make_correspondence_type("Dept Scoping", "TDS")
		user_a = _make_user(
			"test.dept.a@masar-diwan.local", ["Correspondence Employee"], dept_a
		)

		doc = frappe.get_doc(
			{
				"doctype": "Correspondence",
				"correspondence_type": ctype,
				"subject": "Department B only",
				"department": dept_b,
			}
		).insert(ignore_permissions=True)

		try:
			frappe.set_user(user_a)
			self.assertFalse(frappe.has_permission("Correspondence", "read", doc=doc.name))
			visible_names = frappe.get_list(
				"Correspondence", filters={"name": doc.name}, pluck="name"
			)
			self.assertNotIn(doc.name, visible_names)
		finally:
			frappe.set_user("Administrator")

	def test_create_permission_skips_confidentiality_gate(self):
		"""Regression test for the documented create-vs-read fix: creating a
		Highly Confidential Correspondence directly must only be gated by
		department scoping, never by the confidentiality tier itself (that
		tier controls who may *read* it afterwards, not who may register it).
		"""
		dept = _make_department("Test Dept - Create Perm")
		ctype = _make_correspondence_type("Create Perm", "TCP")
		user = _make_user(
			"test.create.perm@masar-diwan.local", ["Diwan Officer"], department=None
		)

		try:
			frappe.set_user(user)
			doc = frappe.get_doc(
				{
					"doctype": "Correspondence",
					"correspondence_type": ctype,
					"subject": "Directly-created Highly Confidential",
					"department": dept,
					"confidentiality": "Highly Confidential",
				}
			)
			self.assertTrue(frappe.has_permission("Correspondence", "create", doc=doc))
		finally:
			frappe.set_user("Administrator")
