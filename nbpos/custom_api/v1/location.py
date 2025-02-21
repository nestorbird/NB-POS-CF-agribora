import frappe

@frappe.whitelist()
def get_location():
    body = frappe.local.form_dict
    if body.get("search_location"):
        filter_condition = f'%{body.get("search_location")}%'
        return frappe.db.sql("""
            SELECT DISTINCT custom_location
            FROM `tabCost Center` WHERE disabled=0 and custom_location LIKE %s
            ORDER BY custom_location ASC;
            """, (filter_condition,) ,as_dict=1)


    elif (body.get("custom_location")):
        base_url = frappe.db.get_single_value('nbpos Setting', 'base_url')
        return frappe.db.sql("""
                SELECT custom_location, custom_address, cost_center_name, name,
                CONCAT(%(base_url)s, custom_attach_image) AS custom_attach_image
                FROM `tabCost Center`
                WHERE disabled = 0 AND custom_location = %(custom_location)s
                ORDER BY creation DESC
                """, {
                    'base_url': base_url,
                    'custom_location': body.get("custom_location")
                }, as_dict=1)


    else:
        return frappe.db.sql("""
            SELECT Distinct(custom_location)
            FROM `tabCost Center` WHERE custom_location is NOT NULL and disabled=0
            ORDER BY custom_location ASC;
            """,as_dict=1)



@frappe.whitelist(allow_guest=True)
def get_all_location_list():
       return frappe.db.sql("""
        SELECT DISTINCT custom_location 
        FROM `tabCost Center` 
        WHERE disabled=0 and custom_location IS NOT NULL
        ORDER BY custom_location ASC;
                """,as_dict=True)