# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from masar_diwan.utils.qrcode_utils import attach_tracking_qr_code


class Envelope(Document):
	def validate(self):
		# party/party_type's own fetch_from (correspondence.party/
		# correspondence.party_type) is Desk-form-JS-only - the same
		# limitation confirmed repeatedly elsewhere in this app (a script,
		# API call, or the Desk grid's own "Add Row" quick-entry flow never
		# triggers it). Recomputed here directly on every save so both
		# columns are correct regardless of how a row was added, instead of
		# only when a user happened to interactively pick "Correspondence"
		# in a live browser.
		correspondences = {row.correspondence for row in self.envelope_documents if row.correspondence}
		party_by_correspondence = {}
		if correspondences:
			party_by_correspondence = {
				c.name: c
				for c in frappe.get_all(
					"Correspondence",
					filters={"name": ["in", list(correspondences)]},
					fields=["name", "party", "party_type"],
				)
			}
		for row in self.envelope_documents:
			info = party_by_correspondence.get(row.correspondence)
			row.party = info.party if info else None
			row.party_type = info.party_type if info else None

	def after_insert(self):
		self.db_set("envelope_no", self.name, update_modified=False)
		attach_tracking_qr_code(self, ref=self.name)

	def on_update(self):
		current = {row.correspondence for row in self.envelope_documents}

		for ref in current:
			frappe.db.set_value("Correspondence", ref, "envelope", self.name)

		previously_linked = frappe.get_all(
			"Correspondence", filters={"envelope": self.name}, pluck="name"
		)
		for ref in previously_linked:
			if ref not in current:
				frappe.db.set_value("Correspondence", ref, "envelope", None)
