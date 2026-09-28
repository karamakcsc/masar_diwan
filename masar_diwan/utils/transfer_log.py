"""Shared helper for logging a Correspondence handling event that isn't
itself a status transition (added to an Envelope, added to a Delivery
Sheet) into the SAME `Correspondence Transfer Log` child table
`Correspondence.log_status_transition()` already writes to - one place a
staff member looks to see everything that happened to a document, in
order, not two separate mechanisms.

Deliberately inserts the child row directly (parent/parenttype/parentfield
set explicitly) rather than loading the full Correspondence document,
appending, and calling save() - that would re-run the *entire*
`Correspondence.validate()` (category/dynamic-field enforcement included)
purely to log an auxiliary event, and could fail for a reason completely
unrelated to enveloping or scheduling a delivery (e.g. a legacy record
missing a now-required dynamic field). A direct child-row insert can't be
blocked by any of that, matching the same reasoning `Envelope.on_update()`/
`DeliverySheet.on_update()` already use for the field link itself
(`frappe.db.set_value`, not a full parent save).
"""

import frappe


def log_transfer_event(correspondence_name: str, action_type: str, note: str):
	next_idx = (frappe.db.count("Correspondence Transfer Log", {"parent": correspondence_name}) or 0) + 1
	frappe.get_doc(
		{
			"doctype": "Correspondence Transfer Log",
			"parenttype": "Correspondence",
			"parentfield": "transfer_log",
			"parent": correspondence_name,
			"idx": next_idx,
			"date": frappe.utils.now_datetime(),
			"action_type": action_type,
			"to_department": frappe.db.get_value("Correspondence", correspondence_name, "department"),
			"user": frappe.session.user,
			"note": note,
		}
	).insert(ignore_permissions=True)
