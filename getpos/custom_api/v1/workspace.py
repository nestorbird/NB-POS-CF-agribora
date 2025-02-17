import frappe
from frappe.model.document import Document

@frappe.whitelist(allow_guest=True)
def workspace_hide():
    frappe.set_user("Administrator")
    workspace_docs = frappe.get_all("Workspace", filters={"name": ["in", ["Buying", "Manufacturing","Assets","Quality","Projects","Support","Website","Tools","Home","ERPNext Settings","Integrations","ERPNext Integrations","Build"]]})
    for doc in workspace_docs:
        workspace = frappe.get_doc("Workspace", doc.name)
        workspace.is_hidden = 1  
        try:
            workspace.save()  
        except Exception as e:
            print(f"Error saving workspace {workspace.name}: {str(e)}") 
        
    frappe.db.commit()  
    
