# Copyright (c) 2026, Masar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from masar_diwan.utils.dynamic_fields import get_active_dynamic_field_rows, get_effective_category
from masar_diwan.utils.numbering import get_next_reference_no
from masar_diwan.utils.qrcode_utils import attach_tracking_qr_code


class Correspondence(Document):
	def autoname(self):
		self.reference_no = get_next_reference_no(self.correspondence_type)
		self.name = self.reference_no

	def validate(self):
		self.log_status_transition()
		self._validate_category()
		self._validate_dynamic_fields()

	def _validate_category(self):
		"""Same server-side enforcement as Correspondence Request's own
		validate() for this exact field pair (category_is_group recompute,
		group-without-sub-category, sub-category leaf/parent mismatch) -
		link_filters/fetch_from/mandatory_depends_on are all Desk-form-JS-only,
		confirmed there and equally true here, needed now that these fields
		are genuinely user-editable on a direct Correspondence (2026-09-25),
		not just read-only display copies.

		The one rule with no equivalent on Correspondence Request: once a
		source_request is set, category/sub-category are locked - editable
		on the very insert that sets both together (register_correspondence()),
		never after. read_only_depends_on already hides the fields in the
		Desk form at that point, but (same Desk-JS-only story) that alone
		can't stop a script/API save from changing them after the fact."""
		self.category_is_group = (
			frappe.db.get_value("Correspondence Category", self.correspondence_category, "is_group")
			if self.correspondence_category
			else 0
		)

		if self.category_is_group and not self.correspondence_sub_category:
			frappe.throw(_("Select a Correspondence Sub Category - the chosen category has sub-categories."))

		if self.correspondence_sub_category:
			sub = frappe.db.get_value(
				"Correspondence Category",
				self.correspondence_sub_category,
				["parent_correspondence_category", "is_group"],
				as_dict=True,
			)
			if sub.parent_correspondence_category != self.correspondence_category or sub.is_group:
				frappe.throw(
					_("{0} is not a valid sub-category of {1}.").format(
						frappe.bold(self.correspondence_sub_category), frappe.bold(self.correspondence_category)
					)
				)

		if self.source_request and not self.is_new():
			before = self.get_doc_before_save()
			if before and (
				before.correspondence_category != self.correspondence_category
				or before.correspondence_sub_category != self.correspondence_sub_category
			):
				frappe.throw(
					_("Category cannot be changed - this Correspondence was registered from an approved request.")
				)

	def _validate_dynamic_fields(self):
		"""Same server-side enforcement as Correspondence Request's own
		_validate_dynamic_fields() (mandatory_depends_on is Desk-form-JS-only,
		confirmed there and equally true here) - needed on this doctype too
		because Correspondence can be created directly, bypassing the
		Correspondence Request tray entirely (System Manager/Diwan Officer
		have direct create permission - see permissions.py's ptype=="create"
		branch), not just via register_correspondence()'s copy-on-approve
		path, where the same fields were already validated on the source
		request before approval was even allowed."""
		for row in get_active_dynamic_field_rows(get_effective_category(self)):
			if row.reqd and not self.get(f"csf_{row.fieldname_slug}"):
				frappe.throw(_("{0} is required.").format(frappe.bold(row.label)))

	def after_insert(self):
		attach_tracking_qr_code(self)

	# (before_status, after_status) -> action_type, matching Correspondence
	# Workflow's own 6 real transitions exactly (see correspondence_workflow.json)
	# rather than inventing separate wording - every value here already has an
	# Arabic translation in translations/ar.csv under its own name (as a
	# workflow action/status), so this needed no new translation work either.
	TRANSITION_ACTION_TYPES = {
		("Draft", "Under Review"): "Submit for Review",
		("Under Review", "Draft"): "Send Back for Revision",
		("Under Review", "Referred / In Progress"): "Referral",
		("Referred / In Progress", "Under Review"): "Return for Review",
		("Referred / In Progress", "Completed"): "Completed",
		("Completed", "Archived"): "Archived",
	}

	def log_status_transition(self):
		"""Append a Transfer Log row whenever status changes, regardless of
		whether the change came from a Workflow Action or a direct save -
		this must not depend on Workflow Transition hooks alone.

		action_type used to be hardcoded to the literal string "Referral" for
		every single transition, regardless of what actually happened -
		confirmed live (2026-09-28) as a real, visible bug: a document driven
		through Under Review -> Referred/In Progress -> Completed showed
		"Referral" for both rows, even though only the first one was an
		actual referral. Now derived from the real (before, after) status
		pair via TRANSITION_ACTION_TYPES, falling back to the generic
		"Status Change" for any pair that doesn't match one of this
		workflow's own defined transitions (e.g. a future workflow change,
		or a direct status edit that skips states).
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
				"action_type": self.TRANSITION_ACTION_TYPES.get((before.status, self.status), "Status Change"),
				"from_user": before.current_owner,
				"to_user": self.current_owner,
				"to_department": self.department,
				"user": frappe.session.user,
				"note": _("Status changed from {0} to {1}").format(before.status, self.status),
			},
		)
