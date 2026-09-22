import frappe
from frappe.utils import now_datetime


def get_next_reference_no(correspondence_type: str) -> str:
	"""Atomically compute the next reference number for a Correspondence Type.

	Locks the matching row in Correspondence Settings' Numbering Rule child
	table (creating it on first use) so concurrent inserts of the same
	Correspondence Type never collide.

	The very first call for a brand-new Correspondence Type has no row yet
	to lock with `FOR UPDATE`, so a MySQL named lock (`GET_LOCK`) keyed on
	the type is held around the whole check-or-create step to serialize
	concurrent first-time creations too.

	Found-and-fixed 2026-09-22: the rule row's own `prefix` column used to
	only be set once, at row creation - editing `Correspondence Type.prefix`
	afterward silently had no effect on numbers actually issued, since every
	later call read `rule.prefix`, never the live master value. Every call
	now re-checks the rule's stored prefix against the Correspondence Type's
	current one (inside the same lock) and updates it first if they've
	drifted, so a prefix edit takes effect on the very next number issued.
	"""
	if not correspondence_type:
		frappe.throw(frappe._("Correspondence Type is required to generate a reference number"))

	year = now_datetime().year
	lock_name = f"masar_diwan_numbering::{correspondence_type}"
	got_lock = frappe.db.sql("select get_lock(%s, 10)", (lock_name,))[0][0]
	if not got_lock:
		frappe.throw(
			frappe._("Could not acquire numbering lock for {0}, please try again").format(
				correspondence_type
			)
		)

	try:
		row = frappe.db.sql(
			"""
			select name, prefix, current_number, reset_yearly, last_reset_year
			from `tabCorrespondence Numbering Rule`
			where parent = %s and parentfield = %s and correspondence_type = %s
			for update
			""",
			("Correspondence Settings", "numbering_rules", correspondence_type),
			as_dict=True,
		)

		if row:
			rule = row[0]
			live_prefix = frappe.db.get_value("Correspondence Type", correspondence_type, "prefix")
			if live_prefix and live_prefix != rule.prefix:
				frappe.db.sql(
					"update `tabCorrespondence Numbering Rule` set prefix = %s where name = %s",
					(live_prefix, rule.name),
				)
				rule.prefix = live_prefix
		else:
			rule = _create_numbering_rule(correspondence_type, year)

		if rule.reset_yearly and rule.last_reset_year != year:
			new_number = 1
		else:
			new_number = (rule.current_number or 0) + 1

		frappe.db.sql(
			"""
			update `tabCorrespondence Numbering Rule`
			set current_number = %s, last_reset_year = %s
			where name = %s
			""",
			(new_number, year, rule.name),
		)
	finally:
		frappe.db.sql("select release_lock(%s)", (lock_name,))

	return f"{rule.prefix}-{year}-{str(new_number).zfill(4)}"


def _create_numbering_rule(correspondence_type: str, year: int) -> frappe._dict:
	prefix = frappe.db.get_value("Correspondence Type", correspondence_type, "prefix")
	if not prefix:
		frappe.throw(
			frappe._("Correspondence Type {0} has no prefix configured").format(correspondence_type)
		)

	name = frappe.generate_hash(length=10)
	last_idx = frappe.db.sql(
		"""select coalesce(max(idx), 0) from `tabCorrespondence Numbering Rule`
		where parent = %s and parentfield = %s""",
		("Correspondence Settings", "numbering_rules"),
	)[0][0]

	frappe.db.sql(
		"""
		insert into `tabCorrespondence Numbering Rule`
			(name, parent, parenttype, parentfield, idx, correspondence_type,
			 prefix, current_number, reset_yearly, last_reset_year,
			 creation, modified, owner, modified_by)
		values
			(%s, %s, 'Correspondence Settings', %s, %s, %s, %s, 0, 1, %s,
			 now(), now(), %s, %s)
		""",
		(
			name,
			"Correspondence Settings",
			"numbering_rules",
			last_idx + 1,
			correspondence_type,
			prefix,
			year,
			frappe.session.user,
			frappe.session.user,
		),
	)

	return frappe._dict(
		name=name,
		prefix=prefix,
		current_number=0,
		reset_yearly=1,
		last_reset_year=year,
	)
