# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Envelope(Document):
	def after_insert(self):
		self.db_set("envelope_no", self.name, update_modified=False)

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
