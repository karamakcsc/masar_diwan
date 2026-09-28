# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from masar_diwan.utils.qrcode_utils import attach_tracking_qr_code
from masar_diwan.utils.transfer_log import log_transfer_event


def on_file_attached(file_doc, method=None):
	"""Registered against File's own after_insert (hooks.py) - a plain
	sidebar attachment never touches DeliverySheet.validate()/on_update()
	at all, so proof_uploaded_on (still a real, useful "when was proof
	first attached" timestamp) can only be tracked from here now that
	there's no dedicated signed_sheet_image field to watch for a
	before/after change on. Only ever set once, on the first attachment -
	later attachments (more than one supporting document is expected,
	the whole reason this replaced the single Attach field) don't move it."""
	if file_doc.attached_to_doctype != "Delivery Sheet" or not file_doc.attached_to_name:
		return
	if not frappe.db.get_value("Delivery Sheet", file_doc.attached_to_name, "proof_uploaded_on"):
		frappe.db.set_value(
			"Delivery Sheet", file_doc.attached_to_name, "proof_uploaded_on", now_datetime()
		)


class DeliverySheet(Document):
	def after_insert(self):
		self.db_set("delivery_sheet_no", self.name, update_modified=False)
		attach_tracking_qr_code(self, ref=self.name)

	def validate(self):
		self.validate_items()
		self.populate_item_details()
		self.validate_receipt_confirmation()

	def validate_items(self):
		"""A row carries either a Correspondence or a whole Envelope (a
		bundle of correspondences delivered together), never both/neither -
		enforced here since a Table row has no framework-level "exactly one
		of these two Links" constraint."""
		for row in self.items:
			if bool(row.correspondence) == bool(row.envelope):
				frappe.throw(
					_("Row {0}: set either Correspondence or Envelope, not both or neither.").format(row.idx)
				)

	def populate_item_details(self):
		for row in self.items:
			if row.correspondence:
				row.subject = frappe.db.get_value("Correspondence", row.correspondence, "subject")
				row.attachment_count = frappe.db.count(
					"File",
					{"attached_to_doctype": "Correspondence", "attached_to_name": row.correspondence},
				)
			else:
				row.subject = _("Envelope {0}").format(row.envelope)
				row.attachment_count = frappe.db.count("Envelope Document", {"parent": row.envelope})

	def validate_receipt_confirmation(self):
		"""Replaces the old dedicated `signed_sheet_image` Attach field -
		staff attach proof via Frappe's own generic file-attachment sidebar
		instead (a delivery can need more than one supporting document, e.g.
		a signed sheet plus an ID scan, which one Attach field could never
		hold), and this just confirms at least one such attachment exists
		before receipt can be confirmed."""
		before = self.get_doc_before_save()
		if not before or before.status == self.status:
			return
		if self.status == "Receipt Confirmed" and not self._has_attachment():
			frappe.throw(_("Attach at least one supporting document (e.g. the signed delivery sheet) before confirming receipt."))

	def _has_attachment(self):
		return frappe.db.count("File", {"attached_to_doctype": "Delivery Sheet", "attached_to_name": self.name}) > 0

	def on_update(self):
		# Linked immediately on being added to the sheet, regardless of
		# status (not gated on "Receipt Confirmed" - that used to mean a
		# Correspondence's own `delivery_sheet` field only reflected reality
		# once delivery was already confirmed, well after staff started
		# actually handling it). Mirrors Envelope.on_update()'s own
		# new-link-only logging and bidirectional clear-on-removal, so a
		# correspondence pulled off a still-pending sheet doesn't keep a
		# stale link either.
		current_correspondences = {row.correspondence for row in self.items if row.correspondence}

		for ref in current_correspondences:
			if frappe.db.get_value("Correspondence", ref, "delivery_sheet") != self.name:
				frappe.db.set_value("Correspondence", ref, "delivery_sheet", self.name)
				log_transfer_event(ref, "Added to Delivery Sheet", _("Added to Delivery Sheet {0}").format(self.name))

		previously_linked = frappe.get_all(
			"Correspondence", filters={"delivery_sheet": self.name}, pluck="name"
		)
		for ref in previously_linked:
			if ref not in current_correspondences:
				frappe.db.set_value("Correspondence", ref, "delivery_sheet", None)

		# Same immediate-link/bidirectional-clear treatment for a whole
		# Envelope placed on this sheet, reusing the field Envelope already
		# had (`linked_delivery_sheet`) but that nothing ever kept in sync
		# before now - no Transfer Log equivalent here, since Envelope has
		# no such child table to log into.
		current_envelopes = {row.envelope for row in self.items if row.envelope}

		for ref in current_envelopes:
			if frappe.db.get_value("Envelope", ref, "linked_delivery_sheet") != self.name:
				frappe.db.set_value("Envelope", ref, "linked_delivery_sheet", self.name)

		previously_linked_envelopes = frappe.get_all(
			"Envelope", filters={"linked_delivery_sheet": self.name}, pluck="name"
		)
		for ref in previously_linked_envelopes:
			if ref not in current_envelopes:
				frappe.db.set_value("Envelope", ref, "linked_delivery_sheet", None)
