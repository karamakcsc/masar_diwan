"""Bounded, permission-aware paging for the Diwan portal lists."""

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import frappe
from frappe.utils import cint

PAGE_SIZE = 50


def get_page(context, doctype, *, fields, filters=None, order_by="modified desc"):
	page = min(10000, max(1, cint(frappe.form_dict.get("page")) or 1))
	rows = frappe.get_list(
		doctype,
		fields=fields,
		filters=filters or {},
		order_by=f"{order_by}, name asc",
		limit_start=(page - 1) * PAGE_SIZE,
		limit_page_length=PAGE_SIZE + 1,
	)
	# Preserve only the filters understood by these list pages. Never carry
	# document-detail parameters into a list link.
	query = {
		key: frappe.form_dict[key]
		for key in ("_lang", "event_type", "result", "channel", "reference_doctype")
		if frappe.form_dict.get(key)
	}

	def page_url(number):
		route = urlsplit(context.active_route)
		params = {**dict(parse_qsl(route.query)), **query, "page": number}
		return urlunsplit(("", "", route.path, urlencode(params), ""))

	context.pagination = {
		"page": page,
		"previous_url": page_url(page - 1) if page > 1 else None,
		"next_url": page_url(page + 1) if len(rows) > PAGE_SIZE else None,
	}
	return rows[:PAGE_SIZE]
