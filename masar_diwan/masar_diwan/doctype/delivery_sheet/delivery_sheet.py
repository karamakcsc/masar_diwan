# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from masar_diwan.utils.transfer_log import log_transfer_event


class DeliverySheet(Document):
	def after_insert(self):
		self.db_set("delivery_sheet_no", self.name, update_modified=False)

	def validate(self):
		self.populate_item_details()
		self.validate_receipt_confirmation()
		self.track_proof_upload()

	def populate_item_details(self):
		for row in self.items:
			row.subject = frappe.db.get_value("Correspondence", row.correspondence, "subject")
			row.attachment_count = frappe.db.count(
				"File",
				{"attached_to_doctype": "Correspondence", "attached_to_name": row.correspondence},
			)

	def validate_receipt_confirmation(self):
		before = self.get_doc_before_save()
		if not before or before.status == self.status:
			return
		if self.status == "Receipt Confirmed" and not self.signed_sheet_image:
			frappe.throw(_("Upload the signed sheet image before confirming receipt"))

	def track_proof_upload(self):
		before = self.get_doc_before_save()
		if before and not before.signed_sheet_image and self.signed_sheet_image:
			self.proof_uploaded_on = now_datetime()

	def on_update(self):
		# Linked immediately on being added to the sheet, regardless of
		# status (not gated on "Receipt Confirmed" - that used to mean a
		# Correspondence's own `delivery_sheet` field only reflected reality
		# once delivery was already confirmed, well after staff started
		# actually handling it). Mirrors Envelope.on_update()'s own
		# new-link-only logging and bidirectional clear-on-removal, so a
		# correspondence pulled off a still-pending sheet doesn't keep a
		# stale link either.
		current = {row.correspondence for row in self.items}

		for ref in current:
			if frappe.db.get_value("Correspondence", ref, "delivery_sheet") != self.name:
				frappe.db.set_value("Correspondence", ref, "delivery_sheet", self.name)
				log_transfer_event(ref, "Added to Delivery Sheet", _("Added to Delivery Sheet {0}").format(self.name))

		previously_linked = frappe.get_all(
			"Correspondence", filters={"delivery_sheet": self.name}, pluck="name"
		)
		for ref in previously_linked:
			if ref not in current:
				frappe.db.set_value("Correspondence", ref, "delivery_sheet", None)
