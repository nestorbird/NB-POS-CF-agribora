import frappe
import json
from frappe import _
import json
STANDARD_USERS = ("Guest", "Administrator")
from erpnext.selling.doctype.customer.customer import get_customer_outstanding

@frappe.whitelist()
def get_customer(mobile_no=None, name=None):
    res = frappe._dict()
    sql = frappe.db.sql(
        """SELECT EXISTS(SELECT * FROM `tabCustomer` WHERE mobile_no = %s OR name = %s)""",
        (mobile_no, name)
    )
    result = sql[0][0]

    if result == 1:
        customer_detail = frappe.db.sql(
            """SELECT name, customer_name, customer_primary_contact, mobile_no, email_id,
            primary_address, hub_manager, loyalty_program FROM `tabCustomer`
            WHERE mobile_no = %s OR name = %s""",
            (mobile_no, name), as_dict=True
        )

        loyalty_point_details = frappe._dict(
            frappe.get_all(
                "Loyalty Point Entry",
                filters={
                    "customer": name,
                    "expiry_date": (">=", frappe.utils.getdate()),
                },
                group_by="company",
                fields=["company", "sum(loyalty_points) as loyalty_points"],
                as_list=1,
            )
        )
        companies = frappe.get_all(
            "Sales Invoice", filters={"docstatus": 1, "customer": name}, distinct=1, fields=["company"]
        )
        loyalty_points = 0
        for d in companies:
            if loyalty_point_details:
                loyalty_points = loyalty_point_details.get(d.company)

        conversion_factor = None
        if customer_detail:
            conversion_factor = frappe.db.get_value(
                "Loyalty Program", {"name": customer_detail[0].loyalty_program}, ["conversion_factor"], as_dict=True
            )

        # Credit limit and outstanding amount logic
        credit_limit = 0
        outstanding_amount = 0

        try:
            # Fetch the customer document
            customer = frappe.get_doc('Customer', customer_detail[0].name)
            credit_limit=customer.custom_credit_limit    
         

            # Fetch the total outstanding amount (total unpaid invoices)
           
            outstanding_amount =  get_customer_outstanding(
			name, frappe.get_doc("Global Defaults").default_company, ignore_outstanding_sales_order=False
		)

        except frappe.DoesNotExistError:
            message = _("Customer not found.")
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), _("Error fetching credit limit"))
            message = _("An error occurred while fetching the credit limit.")

        res['success_key'] = 1
        res['message'] = "success"
        res['customer'] = customer_detail
        res['loyalty_points'] = loyalty_points
        res['conversion_factor'] = conversion_factor.conversion_factor if conversion_factor else 0
        res['loyalty_amount'] = loyalty_points * conversion_factor.conversion_factor if conversion_factor else 0
        res['credit_limit'] = credit_limit
        res['outstanding_amount'] = outstanding_amount
        return res
    else:
        res["success_key"] = 0
        res['mobile_no'] = mobile_no
        res["message"] = "Mobile Number/Customer Does Not Exist"
        return res
    
@frappe.whitelist()
def get_all_customer(search=None, from_date=None):
    res=frappe._dict()
    customer = frappe.qb.DocType('Customer')
    if search:
        query = """SELECT name, customer_name, mobile_no, email_id
        FROM `tabCustomer`
        WHERE disabled = 0 AND mobile_no LIKE %s"""
        params = ("%"+search+"%",)
    else:
        query = """SELECT name, customer_name, mobile_no, email_id
        FROM `tabCustomer`
        WHERE disabled = 0 """
        params = ()
    if from_date:
        query += "AND modified >= %s"
        params += (from_date,)
    customer = frappe.db.sql(query, params, as_dict=1)
    if customer:
        res['success_key'] = 1
        res['message'] = "success"
        res['customer'] = customer
        return res
    else:
        res["success_key"] = 0
        res["message"] = "No customer found"
        res['customer']= customer
        return res
@frappe.whitelist()
def create_customer():
        customer_detail = frappe.request.data
        customer_detail = json.loads(customer_detail)
        res = frappe._dict()
        try:
                if customer_detail.get("mobile_no") and frappe.db.exists({"doctype":"Customer" , 'mobile_no': customer_detail.get("mobile_no") } ):
                                existing_customer = frappe.db.get_value("Customer", {"mobile_no": customer_detail.get("mobile_no")}, ["name", "customer_name", "mobile_no", "email_id"], as_dict=True)
                                res["success_key"] = 0
                                res["message"] = "Customer already present with this mobile no."
                                res["customer"] = existing_customer
                                return res
                else: 
                        customer = frappe.new_doc("Customer")
                        customer.customer_name = customer_detail.get("customer_name")
                        customer.mobile_no = customer_detail.get("mobile_no")
                        customer.email_id = customer_detail.get("email_id")
                        customer.custom_pos_shift = customer_detail.get("pos_opening_shift")
                        customer.customer_group = 'All Customer Groups'
                        customer.territory = 'All Territories'
                        customer.save(ignore_permissions=True)
                        frappe.db.commit()
                        res['success_key'] = 1
                        res['message'] = "success"
                        res["customer"] ={"name" : customer.name,
                                "customer_name": customer.customer_name,
                                "mobile_no" : customer.mobile_no,
                                "email_id":customer.email_id
                                }
                        return res

        except Exception as e:
                frappe.clear_messages()
                frappe.local.response["message"] ={
                        "success_key":0,
                        "message":"Invalid values please check your request parameters"  
                }

@frappe.whitelist()
def edit_customer():
        customer_detail = frappe.request.data
        customer_detail = json.loads(customer_detail)
        frappe.set_user("Administrator")
        res = frappe._dict()
        existing_customer = frappe.db.get_value("Customer", {"mobile_no": customer_detail.get("mobile_no")}, ["name", "customer_name", "mobile_no", "email_id"], as_dict=True)
        if existing_customer and existing_customer.name !=customer_detail.get("name") :                
                res["success_key"] = 0
                res["message"] = "Customer already present with this mobile no."
                res["customer"] = existing_customer
                return res 
        else:
                update_customer = frappe.get_doc("Customer",customer_detail.get("name"))
                frappe.db.sql("update `tabContact` set `mobile_no` =%s  where name=%s",(customer_detail.get("mobile_no"), update_customer.customer_primary_contact))
                update_customer.customer_name = customer_detail.get("customer_name")  
                update_customer.mobile_no = customer_detail.get("mobile_no")
                # Check if customer email is not provided or is an empty string
                if not customer_detail.get("email_id") or customer_detail.get("email_id") == "":
                        email_id = ""
                else:
                        email_id = customer_detail.get("email_id")

                # Update the email_id in the 'tabContact' table
                frappe.db.sql(
                "UPDATE `tabContact` SET `email_id` = %s WHERE name = %s",
                (email_id, update_customer.customer_primary_contact)
                )

                # Set the email_id in the update_customer object
                update_customer.email_id = email_id

                # Save the update_customer object with ignore_permissions=True
                update_customer.save(ignore_permissions=True)               
                res['success_key'] = 1
                res['message'] = "Customer updated successfully"
                res["customer"] ={"name" : customer_detail.get("name") ,
                                "customer_name": customer_detail.get("customer_name") ,
                                "mobile_no" : customer_detail.get("mobile_no") ,
                                "email_id" : customer_detail.get("email_id") 
                                }
                return res
        
