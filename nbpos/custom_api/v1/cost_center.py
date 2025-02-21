import frappe
from nbpos.controllers import frappe_response,handle_exception
import frappe
@frappe.whitelist(allow_guest=True)
def get_cost_center_by_pin():  
        body = frappe.local.form_dict
        pin = body.get("custom_pin")
        cost_center = body.get("cost_center")
        
        if not pin or not cost_center:
                missing_param = "custom_pin" if not pin else "cost_center"
                return frappe_response(400, f"{missing_param} is missing")

        custom_pin = frappe.db.get_value("Cost Center",cost_center,'custom_pin')
        if int(custom_pin) == int(pin):
                return frappe_response(200, {"is_verified": True})
        
        else:
                return frappe_response(200, {"is_verified": False})
  