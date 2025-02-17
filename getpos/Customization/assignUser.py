import frappe

def assign_role(doc, method):
    # Assign the role "GetPos User" to the user
    if not frappe.db.exists("Role", "GetPos User"):
        return
    doc.add_roles("GetPos User")
    
    # Generate an API key if not already generated
    if not doc.api_key:
        doc.api_key = frappe.generate_hash()
        doc.api_secret = frappe.generate_hash()
        doc.save()
