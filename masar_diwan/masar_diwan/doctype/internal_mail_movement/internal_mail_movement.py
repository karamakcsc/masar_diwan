# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_fullname, now_datetime

from masar_diwan.permissions import get_user_departments


class InternalMailMovement(Document):
	def before_insert(self):
		# docfield default="user"/"__user" is only resolved by the Desk
		# new-doc flow - server-side frappe.get_doc(...).insert() needs it
		# set explicitly, same gotcha already documented for
		# Correspondence Request.before_insert(). Uses frappe.utils.get_fullname()
		# rather than frappe.session.user_fullname - the latter is only
		# reliably populated by a real Desk-session bootstrap and was found
		# to be None both via frappe.set_user() and over real HTTP
		# frappe.client.insert (confirmed directly, not assumed).
		if not self.sender_name:
			self.sender_name = get_fullname(frappe.session.user)
		if not self.from_department:
			departments = get_user_departments(frappe.session.user)
			if departments:
				self.from_department = next(iter(departments))

	def on_update(self):
		before = self.get_doc_before_save()
		if not before or before.status == self.status:
			return

		if self.status == "In Transit" and not self.sent_on:
			self.db_set("sent_on", now_datetime(), update_modified=False)

		if self.status == "Received":
			if not self.received_by:
				self.db_set("received_by", get_fullname(frappe.session.user), update_modified=False)
			if not self.received_on:
				self.db_set("received_on", now_datetime(), update_modified=False)
