# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DocumentAccessProfile(Document):
	def validate(self):
		if self.department_field and self.department_field not in self._target_fieldnames():
			frappe.throw(
				frappe._("Department Field {0} does not exist on {1}").format(
					self.department_field, self.document_type
				)
			)
		if self.supports_confidentiality:
			if self.confidentiality_field not in self._target_fieldnames():
				frappe.throw(
					frappe._("Confidentiality Field {0} does not exist on {1}").format(
						self.confidentiality_field, self.document_type
					)
				)

	def _target_fieldnames(self):
		meta = frappe.get_meta(self.document_type)
		return {df.fieldname for df in meta.fields} | set(frappe.model.default_fields)
