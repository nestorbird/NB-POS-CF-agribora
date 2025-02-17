import frappe
from frappe.utils import  cint

def get_delivery_note_serial_no(item_code, qty, delivery_note):
	serial_nos = ""
	dn_serial_nos = frappe.db.sql_list(
		f""" select name from `tabSerial No`
		where item_code = %(item_code)s and delivery_document_no = %(delivery_note)s
		and sales_invoice is null limit {cint(qty)}""",
		{"item_code": item_code, "delivery_note": delivery_note},
	)

	if dn_serial_nos and len(dn_serial_nos) > 0:
		serial_nos = "\n".join(dn_serial_nos)

	return serial_nos