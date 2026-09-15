import base64
import io

import frappe
import qrcode
from frappe.utils import get_url
from frappe.utils.file_manager import save_file


def attach_tracking_qr_code(doc, url_path="/track"):
	"""Generate a QR code encoding the tracking URL for `doc` and attach it
	as a private file, storing the file URL on `doc.qr_code`.
	"""
	tracking_url = get_url(f"{url_path}?ref={doc.reference_no}")

	img = qrcode.make(tracking_url)
	buffer = io.BytesIO()
	img.save(buffer, format="PNG")
	content = buffer.getvalue()

	file_doc = save_file(
		fname=f"{frappe.scrub(doc.reference_no)}-qr.png",
		content=content,
		dt=doc.doctype,
		dn=doc.name,
		df="qr_code",
		is_private=1,
	)

	doc.db_set("qr_code", file_doc.file_url, update_modified=False)


def qr_data_uri(text: str) -> str:
	"""Render `text` as a QR code and return it as a base64 data: URI, for
	use directly in a Print Format's <img src="..."> without needing a
	stored File (used by Delivery Sheet / Envelope / Document labels).
	"""
	img = qrcode.make(text)
	buffer = io.BytesIO()
	img.save(buffer, format="PNG")
	encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
	return f"data:image/png;base64,{encoded}"
