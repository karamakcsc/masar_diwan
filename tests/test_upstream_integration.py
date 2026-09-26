"""Run with the bench Python: python -m unittest discover -s tests -p 'test_*.py'.
These regression checks use Frappe's local context and mocks; no database or site writes.
"""
import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import frappe
from masar_diwan.utils.portal_pagination import get_page
from masar_diwan.permissions import get_user_departments


class UpstreamIntegrationTests(unittest.TestCase):
	def setUp(self):
		frappe.local.form_dict = frappe._dict()
		frappe.local.flags = frappe._dict()
		frappe.local.session = frappe._dict(user="requester@example.test")
		frappe.local.db = SimpleNamespace()

	def test_portal_messages_are_scoped_and_honor_overrides(self):
		from masar_diwan.utils import portal_i18n
		frappe.local.lang = "ar"
		with patch.object(portal_i18n, "get_translations_from_apps", return_value={"Register": "تسجيل"}) as load, patch.object(frappe, "_", return_value="تسجيل مخصص"):
			self.assertEqual(portal_i18n.get_portal_messages(), {"Register": "تسجيل مخصص"})
			load.assert_called_once_with("ar", apps=["masar_diwan"])

	def test_tab_pagination_preserves_filters_and_language(self):
		frappe.form_dict.update(tab="audit_log", page="2", result="Denied", _lang="ar", name="not-a-list-filter")
		context = frappe._dict(active_route="/diwan/queue?tab=audit_log")
		with patch.object(frappe, "get_list", return_value=[{}] * 51) as query:
			self.assertEqual(len(get_page(context, "Access Log Entry", fields=["name"])), 50)
			self.assertEqual(query.call_args.kwargs["limit_start"], 50)
		self.assertEqual(parse_qs(urlsplit(context.pagination["next_url"]).query), {
			"tab": ["audit_log"], "page": ["3"], "result": ["Denied"], "_lang": ["ar"]
		})

	def test_pagination_bounds_and_empty_page(self):
		context = frappe._dict(active_route="/diwan/requests")
		frappe.form_dict.page = "-20"
		with patch.object(frappe, "get_list", return_value=[]):
			self.assertEqual(get_page(context, "Correspondence Request", fields=["name"]), [])
		self.assertEqual(context.pagination["page"], 1)
		self.assertIsNone(context.pagination["previous_url"])
		self.assertIsNone(context.pagination["next_url"])

	def test_legacy_redirects_preserve_supported_query(self):
		for tab in ("submit", "tray", "delivery_sheets", "envelopes", "audit_log"):
			with self.subTest(tab=tab):
				frappe.form_dict.update(name="طلب & 1", _lang="ar", page="2", result="Denied", arbitrary="drop")
				module = importlib.import_module(f"masar_diwan.www.diwan.{tab}.index")
				with self.assertRaises(frappe.Redirect):
					module.get_context(frappe._dict())
				url = urlsplit(frappe.local.flags.redirect_location)
				self.assertEqual(url.path, "/diwan/requests" if tab == "submit" else "/diwan/queue")
				query = parse_qs(url.query)
				self.assertEqual(query["tab"], [tab])
				self.assertEqual(query["name"], ["طلب & 1"])
				self.assertNotIn("arbitrary", query)

	def test_employee_department_is_authoritative(self):
		frappe.local.db = SimpleNamespace(exists=lambda *a: True, get_value=lambda *a, **k: "HR Department")
		with patch.object(frappe, "get_all") as fallback:
			self.assertEqual(get_user_departments("employee@example.test"), {"HR Department"})
			fallback.assert_not_called()

	def test_department_fallback_without_active_employee(self):
		frappe.local.db = SimpleNamespace(exists=lambda *a: True, get_value=lambda *a, **k: None)
		with patch.object(frappe, "get_all", return_value=["Assigned Department"]):
			self.assertEqual(get_user_departments("employee@example.test"), {"Assigned Department"})

	def test_envelope_search_without_permission_is_empty(self):
		from masar_diwan.api.portal import search_envelopes
		with patch.object(frappe, "has_permission", return_value=False), patch.object(frappe, "get_list") as query:
			self.assertEqual(search_envelopes("ENV"), [])
			query.assert_not_called()

	def test_staff_cannot_read_another_owners_draft(self):
		from masar_diwan import permissions
		doc = frappe._dict(doctype="Correspondence Request", name="draft", owner="other@example.test", status="Draft")
		profile = frappe._dict(department_exempt_roles=[frappe._dict(role="Diwan Officer")])
		frappe.local.db = SimpleNamespace(escape=lambda v: repr(v))
		with patch.object(frappe, "get_roles", return_value=["Diwan Officer"]), patch.object(permissions, "_get_profile", return_value=profile), patch.object(permissions, "_log_denial"):
			self.assertFalse(permissions.has_permission_correspondence_request(doc))
			self.assertIn("status != 'Draft'", permissions.get_permission_query_conditions_correspondence_request())
			doc.owner = frappe.session.user
			self.assertTrue(permissions.has_permission_correspondence_request(doc))
			doc.owner = "other@example.test"
			doc.status = "Pending Review"
			self.assertTrue(permissions.has_permission_correspondence_request(doc))


if __name__ == "__main__":
	unittest.main()
