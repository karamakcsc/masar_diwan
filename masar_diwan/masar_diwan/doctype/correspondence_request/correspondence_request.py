# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from masar_diwan.access_log import log_event
from masar_diwan.permissions import get_user_departments


class CorrespondenceRequest(Document):
	def validate(self):
		# category_is_group backs correspondence_sub_category's
		# depends_on/mandatory_depends_on. Its docfield fetch_from
		# (correspondence_category.is_group) only ever runs client-side, the
		# moment a real browser session changes the field - any server-side
		# path (frappe.client.insert, a script, the portal/Desk-Page custom
		# forms that build their own payload) never triggers it at all, so
		# this recomputes it directly on every save regardless of how the
		# document got here, rather than trusting whatever the client sent.
		self.category_is_group = (
			frappe.db.get_value("Correspondence Category", self.correspondence_category, "is_group")
			if self.correspondence_category
			else 0
		)

		# mandatory_depends_on (set on this field in the DocType JSON) is
		# Desk-form-JS-only - confirmed directly against Frappe core
		# (BaseDocument._get_missing_mandatory_fields() only ever looks at
		# the static `reqd` flag, never mandatory_depends_on) - so without an
		# explicit check here, any non-Desk-form save (the portal, the
		# custom "New Request" Desk Page, a script) could save a group
		# category with no sub-category chosen at all.
		if self.category_is_group and not self.correspondence_sub_category:
			frappe.throw(_("Select a Correspondence Sub Category - the chosen category has sub-categories."))

	def before_insert(self):
		# docfield default="user" is only resolved by the Desk new-doc flow;
		# server-side frappe.get_doc(...).insert() needs it set explicitly.
		if not self.requested_by:
			self.requested_by = frappe.session.user
		if not self.request_date:
			self.request_date = now_datetime()
		if not self.requesting_department:
			departments = get_user_departments(self.requested_by or frappe.session.user)
			if departments:
				self.requesting_department = next(iter(departments))

	def on_update(self):
		before = self.get_doc_before_save()
		if not before or before.status == self.status:
			return

		if before.status == "Under Review" and self.status in (
			"Approved & Numbered",
			"Rejected",
			"Needs Revision",
		):
			log_event(
				"Tray Decision",
				reference_doctype="Correspondence Request",
				reference_name=self.name,
				reason=self.status,
			)

		if self.status == "Approved & Numbered" and not self.resulting_correspondence:
			self.register_correspondence()

	def register_correspondence(self):
		if not self.correspondence_type:
			frappe.throw(
				_("Set a Correspondence Type before approving - it determines the reference number series.")
			)

		correspondence = frappe.get_doc(
			{
				"doctype": "Correspondence",
				"correspondence_type": self.correspondence_type,
				"subject": self.subject,
				"document_date": self.request_date,
				"confidentiality": self.suggested_confidentiality or "Normal",
				"priority": self.suggested_priority or "Normal",
				"department": self.requesting_department,
				"current_owner": self.requested_by,
				"source_request": self.name,
			}
		)
		correspondence.insert(ignore_permissions=True)
		self.db_set("resulting_correspondence", correspondence.name)
