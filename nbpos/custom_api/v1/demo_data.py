import frappe
from frappe.utils import get_url

@frappe.whitelist(allow_guest=True)
def create_cost_center():
    from frappe.utils.file_manager import save_file
    image_path = "./assets/getpos/images/bootle.jpeg"
    try:
        frappe.flags.mute_messages = True
        isDemoSetup = int(frappe.db.get_single_value('nbpos Setting', 'is_demo_setup'))
        if isDemoSetup==1:
            return
 
        company = frappe.get_single('Global Defaults')  
        company_name = company.default_company
        company_doc = frappe.get_doc("Company", company_name)  
        company_abbr = company_doc.abbr  
        cost_center = frappe.get_doc({
            'doctype': 'Cost Center',
            'cost_center_name': f'Default Store', 
            'parent_cost_center': f'{company_name} - {company_abbr}',  
            'is_group': 0, 
            'is_active': 1,
            'custom_location': "Head Office" 
        })
        
        cost_center.insert(ignore_permissions=True)
        warehouse = frappe.get_doc({
            'doctype': 'Warehouse',
            'warehouse_name': f'Default Store', 
            'parent_warehouse': f'Stores - {company_abbr}', 
            'is_group': 0,
            'custom_cost_center':f'Default Store - {company_abbr}' 
        })
        
       
        warehouse.insert(ignore_permissions=True)
        
        pos_profile = frappe.get_doc({
            'doctype': 'POS Profile',
            'name': 'Default', 
            'warehouse': f'Default Store - {company_abbr}', 
            "write_off_cost_center": f'Default Store - {company_abbr}',  
            "write_off_account": f"Write Off - {company_abbr}",  
            'payments': [  # Payments child table
                {
                    'default': 1,
                    "mode_of_payment": "Cash",
                    "allow_in_return": 1  
                }
            ]
        })
        
        
        pos_profile.insert(ignore_permissions=True)
        with open(image_path, "rb") as logo_file:
            file_data = logo_file.read()
        
        file_doc = save_file(
        fname=image_path.split("/")[-1],  
        content=file_data,
        dt=None, 
        dn=None, 
        folder="Home/Attachments", 
        is_private=0 
    )
        bootle_url = file_doc.file_url

       
        item = frappe.get_doc({
            'doctype': 'Item',
            'item_code': 'Dummy Item 1', 
            'item_name': 'Dummy Item 1',  
            'item_group': 'Consumable', 
            'stock_uom': 'Nos',  
            'is_stock_item': 1,  
            'is_sales_item': 1, 
            'is_purchase_item': 1, 
            'valuation_rate': 100,
            'standard_rate': 100,
            'custom_web': 1,
            'custom_pos': 1,
            'custom_kiosk': 1,
            'custom_cost_center': f'Default Store - {company_abbr}',
            'image':bootle_url
        })
        
       
        item.insert(ignore_permissions=True)

        
        stock_entry = frappe.get_doc({
            'doctype': 'Stock Entry',
            'stock_entry_type': 'Material Receipt', 
            'items': [{
                'item_code': item.item_code,
                'qty': 100,
                't_warehouse': f'Default Store - {company_abbr}',  
            }]
        })
        
       
        stock_entry.insert(ignore_permissions=True)  
        
        stock_entry.submit()  
        customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": "Dummy Customer",
        "customer_type": "Individual",
        "customer_group": "All Customer Groups",
        "territory": "All Territories",
        "mobile_no": "9999900001"  
    })
        customer.insert()

        contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": "John Doe",
        "mobile_no": "9999900001",  
        "links": [{
            "link_doctype": "Customer",
            "link_name": customer.name
        }]
    })
        contact.insert(ignore_permissions=True)
        frappe.db.set_value('nbpos Setting', None, 'is_demo_setup', 1)
        frappe.db.set_value('nbpos Setting', None, 'base_url', get_url())
        frappe.db.commit()
             
        return 
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Create Cost Center, Warehouse and POS Profile Error')
        return 
    finally:
        frappe.flags.mute_messages = False  



def upload_logo_and_set():
 
    from frappe.utils.file_manager import save_file
    logo_image_path = "./assets/getpos/images/logo1.png"

    # Upload the logo image
    try:
        frappe.flags.mute_messages = True
        with open(logo_image_path, "rb") as logo_file:
            file_data = logo_file.read()

   
        file_doc = save_file(
        fname=logo_image_path.split("/")[-1],
        content=file_data,
        dt=None,  
        dn=None, 
        folder="Home/Attachments", 
        is_private=0  
    )

     
        logo_url = file_doc.file_url

    
        website_settings = frappe.get_doc("Website Settings", "Website Settings")
        website_settings.app_logo = logo_url 
        website_settings.splash_image=logo_url
        website_settings.favicon=logo_url
        website_settings.app_name="GETPOS"
        website_settings.save(ignore_permissions=True)

        # Commit the changes
        frappe.db.commit()

        # Clear cache to reflect changes
        frappe.clear_cache()
        print(f"Logo uploaded successfully and set in Website Settings: {logo_url}")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        frappe.flags.mute_messages = False  