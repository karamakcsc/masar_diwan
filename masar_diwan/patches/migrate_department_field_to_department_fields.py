import frappe


def execute():
	"""Document Access Profile.department_field (single Data field) was
	replaced by department_fields (a child table, OR semantics across
	multiple fields) to support doctypes like Internal Mail Movement that
	have two department Link fields (from_department/to_department) rather
	than one. Migrate any existing single-field configuration into the new
	table shape before the old column becomes orphaned (Frappe's schema
	sync never drops removed columns - it's still there to read via raw
	SQL immediately after this patch's own doctype-sync step, but won't be
	once anything else touches it).

	Runs post_model_sync, so the new `department_fields` child table
	already exists to insert into by the time this runs.
	"""
	if not frappe.db.table_exists("Document Access Profile"):
		return
	if "department_field" not in frappe.db.get_table_columns("Document Access Profile"):
		return  # already migrated (or a fresh install that never had the old column)

	rows = frappe.db.sql(
		"select name, department_field from `tabDocument Access Profile` "
		"where department_field is not null and department_field != ''",
		as_dict=True,
	)
	for row in rows:
		exists = frappe.db.exists(
			"Document Access Profile Department Field",
			{"parent": row.name, "parenttype": "Document Access Profile", "fieldname": row.department_field},
		)
		if exists:
			continue
		doc = frappe.get_doc("Document Access Profile", row.name)
		doc.append("department_fields", {"fieldname": row.department_field})
		doc.save(ignore_permissions=True)

	frappe.db.commit()
