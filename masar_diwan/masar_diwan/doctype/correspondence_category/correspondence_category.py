# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class CorrespondenceCategory(Document):
	def validate(self):
		for row in self.dynamic_fields:
			if row.definition_mode == "Reuse Existing Field":
				self._resolve_reused_field(row)
			elif not row.fieldname_slug:
				row.fieldname_slug = self._generate_fieldname_slug(row.label)

	def _resolve_reused_field(self, row):
		if not row.reuse_fieldname_slug:
			frappe.throw(
				_("Row {0}: choose an existing field name to reuse, or switch back to New Field.").format(row.idx)
			)
		existing = frappe.db.get_value(
			"Correspondence Category Field",
			{"fieldname_slug": row.reuse_fieldname_slug},
			["fieldtype", "options", "link_scope", "label"],
			as_dict=True,
		)
		if not existing:
			frappe.throw(
				_("Row {0}: no existing field named {1} was found on any category.").format(
					row.idx, frappe.bold(row.reuse_fieldname_slug)
				)
			)
		# Taken from the existing definition, not whatever this row's own
		# Field Type/Options happened to be set to - a shared column can only
		# have one real shape; the row that first defined it is the source
		# of truth, every later "reuse" row just points at it.
		row.fieldname_slug = row.reuse_fieldname_slug
		row.fieldtype = existing.fieldtype
		row.options = existing.options
		row.link_scope = existing.link_scope

	def _generate_fieldname_slug(self, label):
		for _attempt in range(5):
			ascii_part = re.sub(r"[^a-zA-Z0-9]+", "_", label or "").strip("_").lower()
			# Deliberately not the sole basis of the slug even when it comes
			# out readable: labels are frequently Arabic, which scrub()-style
			# slugifying would leave as literal non-ASCII text - safe as a
			# document *name*, but risky baked forever into a DB *column*
			# name (quoting/tooling edge cases some MySQL clients still get
			# wrong). Falls back to a plain random id when the label has no
			# ASCII content at all, and always adds the random suffix
			# regardless, for uniqueness.
			candidate = f"{ascii_part or 'field'}_{frappe.generate_hash(length=6)}"
			if not frappe.db.exists("Correspondence Category Field", {"fieldname_slug": candidate}):
				return candidate
		frappe.throw(_("Could not generate a unique field name - please try saving again."))
