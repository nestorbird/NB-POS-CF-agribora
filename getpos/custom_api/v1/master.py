import frappe
@frappe.whitelist(allow_guest=True)
def get_web_theme_settings():
    theme_settings = frappe.get_doc("Web Theme Settings")
    theme_settings_dict = {}
    theme = frappe.get_meta("Web Theme Settings")
    
    nbpos_setting = frappe.get_doc("nbpos Setting")
    instance_url = nbpos_setting.base_url

    image_fields = [
        "web_logo_image", 
        "web_banner_image", 
        "web_outlet_details_banner_image", 
        "web_footer_logo"
    ]
    
    for field in theme.fields:
        value = theme_settings.get(field.fieldname)
        
        if field.fieldname in image_fields and value:
            if not value.startswith(instance_url):
                value = f"{instance_url.rstrip('/')}/{value.lstrip('/')}"
        
        theme_settings_dict[field.fieldname] = value
    currency = frappe.get_doc("Global Defaults").default_currency
    currency_symbol=frappe.get_doc("Currency",currency).symbol
    theme_settings_dict['default_currency']=currency
    theme_settings_dict['currency_symbol']=currency_symbol    
    theme_settings_dict['default_company']=frappe.get_doc("Global Defaults").default_company    
    res = {
        "data": theme_settings_dict
    }
    return res

@frappe.whitelist(allow_guest=True)
def get_theme_settings():
    theme_settings = frappe.get_doc("Theme Settings")
    theme_settings_dict = {}
    theme = frappe.get_meta("Theme Settings")
    
    nbpos_setting = frappe.get_doc("nbpos Setting")
    instance_url = nbpos_setting.base_url

    image_fields = [
        "app_background_image", 
        "merchant_background_image", 
        "banner_image"
    ]
    
    for field in theme.fields:
        value = theme_settings.get(field.fieldname)
        
        if field.fieldname in image_fields and value:
            if not value.startswith(instance_url):
                value = f"{instance_url.rstrip('/')}/{value.lstrip('/')}"
        
        theme_settings_dict[field.fieldname] = value
    currency = frappe.get_doc("Global Defaults").default_currency
    currency_symbol=frappe.get_doc("Currency",currency).symbol
    theme_settings_dict['default_currency']=currency
    theme_settings_dict['currency_symbol']=currency_symbol    
    theme_settings_dict['default_company']=frappe.get_doc("Global Defaults").default_company
    res = {
        "data": theme_settings_dict
    }
    return res

@frappe.whitelist(allow_guest=True)
def get_abbr(string):
    abbr = ''.join(c[0] for c in string.split()).upper()
    return abbr

@frappe.whitelist(allow_guest=True)
def terms_and_conditions():
        terms_and_condition = frappe.db.sql("""
                SELECT terms
                FROM `tabTerms and Conditions`
                WHERE disabled = 0
        """)[0][0]
        return terms_and_condition


@frappe.whitelist(allow_guest=True)
def privacy_policy_and_terms():
        privacy_policy_and_terms = frappe.db.sql("""
                SELECT privacy_policy,terms_and_conditions
                FROM `tabPrivacy Policy and Terms`
                WHERE disabled = 0
        """)
        res = {"success_key":1,
                "message":"success",
                "Privacy_Policy":privacy_policy_and_terms[0][0],
                "Terms_and_Conditions":privacy_policy_and_terms[0][1]}
        if res["Privacy_Policy"]=="" or res["Terms_and_Conditions"]=="":
                return {
            "success_key":0,
            "message":"no value found for privacy policy and terms"
        }
        return res
@frappe.whitelist()
def clear_demo_data():
        res = frappe._dict()
        company = frappe.db.get_single_value("Global Defaults", "demo_company")
        try:
                tdr = frappe.new_doc("Transaction Deletion Record")
                tdr.company=company
                tdr.process_in_single_transaction = True
                tdr.save(ignore_permissions=True)
                tdr.submit()
                tdr.start_deletion_tasks()
                frappe.db.commit()
                frappe.db.set_single_value("Global Defaults", "demo_company", "")
                frappe.delete_doc("Company", company, ignore_permissions=True)
                frappe.db.commit()
                res['success_key'] = 1
                res['message'] = "Demo company and transactional data deleted successfully."  
        except Exception as e:
                res['success_key'] = 0
                res['message'] = e 
        return res

def after_request(whitelisted, response):
    try:
        kdsurl = frappe.db.get_single_value("Web Theme Settings", "kdsurl")
        if kdsurl:
            response.headers['Access-Control-Allow-Origin'] = kdsurl
        else:
                pass
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS,DELETE,PUT'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "CORS Middleware Error")
    
    return response 