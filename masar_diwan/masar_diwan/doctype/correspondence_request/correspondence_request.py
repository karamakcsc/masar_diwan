# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from masar_diwan.access_log import log_event
from masar_diwan.permissions import get_user_departments


class CorrespondenceRequest(Document):
	def before_insert(self):
		# docfield default="user" is only resolved by the Desk new-doc flow;
		# server-side frappe.get_doc(...).insert() needs it set explicitly.
		if not self.requested_by:
			self.requested_by = frappe.session.user
		if not self.request_date:
			self.request_date = now_datetime()
		if not self.department:
			departments = get_user_departments(self.requested_by or frappe.session.user)
			if departments:
				self.department = next(iter(departments))

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
				"department": self.department,
				"current_owner": self.requested_by,
				"source_request": self.name,
			}
		)
		correspondence.insert(ignore_permissions=True)
		self.db_set("resulting_correspondence", correspondence.name)
