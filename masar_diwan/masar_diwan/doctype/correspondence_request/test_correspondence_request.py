# Copyright (c) 2026, Masar and Contributors
# See license.txt

"""Real integration test for the Diwan Tray's core promise: approving a
Correspondence Request produces a properly-numbered Correspondence, linked
back via source_request. NOT executed against a live bench in this session
(no Frappe site/DB available here) - run with `bench --site <site>
run-tests --app masar_diwan --module
masar_diwan.masar_diwan.doctype.correspondence_request.test_correspondence_request`
before trusting it.
"""

import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests import IntegrationTestCase


def _make_correspondence_type(title, prefix):
	name = f"Test {title}"
	if frappe.db.exists("Correspondence Type", name):
		return name
	doc = frappe.get_doc({"doctype": "Correspondence Type", "title": name, "prefix": prefix})
	doc.insert(ignore_permissions=True)
	return doc.name


class IntegrationTestCorrespondenceRequest(IntegrationTestCase):
	"""
	Integration tests for CorrespondenceRequest.
	Use this class for testing interactions between multiple components.
	"""

	def test_approve_and_register_produces_numbered_correspondence(self):
		ctype = _make_correspondence_type("CRN Approve Flow", "TCA")

		request = frappe.get_doc(
			{
				"doctype": "Correspondence Request",
				"request_type": "Incoming",
				"subject": "End-to-end approve test",
			}
		).insert(ignore_permissions=True)

		apply_workflow(request, "Submit")
		request.reload()
		self.assertEqual(request.status, "Pending Review")

		apply_workflow(request, "Start Review")
		request.reload()
		self.assertEqual(request.status, "Under Review")

		request.correspondence_type = ctype
		request.save(ignore_permissions=True)

		apply_workflow(request, "Approve & Register")
		request.reload()

		self.assertEqual(request.status, "Approved & Numbered")
		self.assertTrue(request.resulting_correspondence)

		correspondence = frappe.get_doc("Correspondence", request.resulting_correspondence)
		self.assertEqual(correspondence.source_request, request.name)
		self.assertTrue(correspondence.name.startswith("TCA-"))

	def test_register_correspondence_requires_type_first(self):
		"""correspondence_request.py::register_correspondence() explicitly
		throws if correspondence_type isn't set yet - a request must not be
		silently approvable into a Correspondence with no numbering series
		to draw from.
		"""
		request = frappe.get_doc(
			{
				"doctype": "Correspondence Request",
				"request_type": "Outgoing",
				"subject": "Missing type on approval",
			}
		).insert(ignore_permissions=True)

		apply_workflow(request, "Submit")
		apply_workflow(request, "Start Review")

		with self.assertRaises(frappe.ValidationError):
			apply_workflow(request, "Approve & Register")
