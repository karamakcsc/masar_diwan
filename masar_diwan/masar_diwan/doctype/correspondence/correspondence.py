# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from masar_diwan.utils.numbering import get_next_reference_no
from masar_diwan.utils.qrcode_utils import attach_tracking_qr_code


class Correspondence(Document):
	def autoname(self):
		self.reference_no = get_next_reference_no(self.correspondence_type)
		self.name = self.reference_no

	def validate(self):
		self.log_status_transition()

	def after_insert(self):
		attach_tracking_qr_code(self)

	def log_status_transition(self):
		"""Append a Transfer Log row whenever status changes, regardless of
		whether the change came from a Workflow Action or a direct save -
		this must not depend on Workflow Transition hooks alone.
		"""
		if self.is_new():
			return

		before = self.get_doc_before_save()
		if not before or before.status == self.status:
			return

		# from_user/to_user reflect current_owner before/after this save; they
		# only change when a transition also reassigns current_owner (e.g. a
		# referral dialog). `user` is always the actor who made the change.

		self.append(
			"transfer_log",
			{
				"date": now_datetime(),
				"action_type": "Referral",
				"from_user": before.current_owner,
				"to_user": self.current_owner,
				"to_department": self.department,
				"user": frappe.session.user,
				"note": _("Status changed from {0} to {1}").format(before.status, self.status),
			},
		)
