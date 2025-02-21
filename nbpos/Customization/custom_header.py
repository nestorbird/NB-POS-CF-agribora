import frappe

def set_user_active():
    from frappe.website.utils import clear_cache
    clear_cache()
    # frappe.cache.set_value(frappe.session.csrf_token, frappe.session.csrf_token)


def set_user_inactive():
    frappe.cache.delete_key(frappe.session.csrf_token)
