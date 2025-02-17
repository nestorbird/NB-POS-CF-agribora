import frappe
import json
from frappe import _
import json
from frappe.utils import cint
STANDARD_USERS = ("Guest", "Administrator")
from frappe.utils import (cint,nowdate, flt)

from frappe.utils import add_to_date, now
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

from getpos.custom_api.v1.sales_invoice import create_sales_invoice_from_sales_order
from getpos.custom_api.v1.warehouse import get_warehouse_for_cost_center

@frappe.whitelist()
def create_sales_order():
        order_list = frappe.request.data
        order_list = json.loads(order_list)
        order_list = order_list["order_list"]
        try:
                res= frappe._dict()
                sales_order = frappe.new_doc("Sales Order")
                sales_order.hub_manager = order_list.get("hub_manager")
                sales_order.ward = order_list.get("ward")
                sales_order.customer = order_list.get("customer")
                arr = order_list.get("transaction_date").split(" ")
                sales_order.transaction_date = arr[0]
                sales_order.transaction_time = arr[1]
                sales_order.delivery_date = order_list.get("delivery_date")
                sales_order = add_items_in_order(sales_order, order_list.get("items"), order_list)
                sales_order.status = order_list.get("status")
                sales_order.mode_of_payment = order_list.get("mode_of_payment")
                sales_order.mpesa_no = order_list.get("mpesa_no")
                sales_order.coupon_code = order_list.get("coupon_code")
                
                sales_order.save()
                sales_order.submit()

                res['success_key'] = 1
                res['message'] = "success"
                res["sales_order"] ={
                       "name" : sales_order.name,
                        "doc_status" : sales_order.docstatus
                        }
                if frappe.local.response.get("exc_type"):
                        del frappe.local.response["exc_type"]
                return res

        except Exception as e:
                if frappe.local.response.get("exc_type"):
                        del frappe.local.response["exc_type"]

                frappe.clear_messages()
                
                frappe.local.response["message"] ={
                "success_key":0,
                "message":e
                        }


def add_items_in_order(sales_order, items, order_list):
        sales_taxes = {}
        for item in items:
                item_tax_template = ""
                if item.get('tax'):
                        item_tax_template = item.get('tax')[0].get('item_tax_template')
                        for tax in item.get('tax'):
                                if sales_taxes.get(tax.get('tax_type')):
                                        sales_taxes[f"{tax.get('tax_type')}"] = flt(sales_taxes[f"{tax.get('tax_type')}"]) + tax.get('tax_amount')
                                else:
                                        sales_taxes.update({f"{tax.get('tax_type')}": tax.get('tax_amount')})

                sales_order.append("items", {
                        "item_code": item.get("item_code"),
                        "qty": item.get("qty"),
                        "rate": item.get("rate"), 
                        "discount_percentage":100 if item.get("rate")==0 else 0,  
                        "custom_parent_item":item.get("custom_parent_item"),
                        "custom_is_attribute_item":item.get("custom_is_attribute_item"),
                        "custom_is_combo_item":item.get("custom_is_combo_item"),
                        "allow_zero_evaluation_rate":item.get("allow_zero_evaluation_rate"),                    
                        "item_tax_template": item_tax_template if item_tax_template else "" ,
                        "custom_ca_id":item.get("custom_ca_id")                
                })

                # if item.get("sub_items"):
                #         for extra_item in item.get("sub_items"):
                #               if extra_item.get('tax'):
                #                      extra_item_tax_template = extra_item.get('tax')[0].get('item_tax_template')
                #               sales_order.append("items", {
                #                 "item_code": extra_item.get("item_code"),
                #                 "qty": extra_item.get("qty"),
                #                 "rate": extra_item.get("rate"),
                #                 "associated_item": item.get('item_code'),
                #                 "item_tax_template": extra_item_tax_template if extra_item_tax_template else "" 
                #                })
        
        for key,value in sales_taxes.items():
               sales_order.append("taxes", {"charge_type": "On Net Total", "account_head": key, "tax_amount": value, "description": key, })


        if order_list.get('tax'):
               for tax in order_list.get('tax'):
                        sales_order.append("taxes", {"charge_type": "On Net Total", "account_head": tax.get('tax_type'), "tax_amount": tax.get('tax_amount'),
                                                      "description": tax.get('tax_type'), "rate": tax.get('tax_rate')})
        
         

        return sales_order

@frappe.whitelist(allow_guest=True)
def create_sales_order_kiosk():
    order_list = frappe.request.data
    order_list = json.loads(order_list)
    order_list = order_list["order_list"]
    
    try:
        frappe.set_user("Administrator")
        res = frappe._dict()
        sales_order = frappe.new_doc("Sales Order")
        sales_order.hub_manager = order_list.get("hub_manager")
        sales_order.custom_source = order_list.get("source")
        sales_order.ward = order_list.get("ward")
        sales_order.custom_order_request = order_list.get("order_request")
        
        if order_list.get("source") == "WEB":
            phone_no = frappe.db.sql("""SELECT phone FROM `tabContact Phone` WHERE phone = %s """, (order_list.get('mobile')))
            if phone_no:
                parent = frappe.db.get_value('Contact Phone', {'phone': order_list.get('mobile')}, 'parent')
                customer = frappe.db.get_value('Dynamic Link', {'parent': parent, 'link_doctype': 'Customer'}, 'link_name')
                if customer:
                    sales_order.customer = customer
            else:
                new_customer = frappe.new_doc("Customer")
                new_customer.customer_name = order_list.get("name")
                new_customer.customer_group = "Individual"
                new_customer.territory = "All Territories"
                new_customer.email_id = order_list.get("email")
                new_customer.mobile_no = order_list.get("mobile")
                new_customer.insert(ignore_permissions=True)
                sales_order.customer = new_customer.name
        else:
            sales_order.customer = order_list.get("customer")
        
        arr = order_list.get("transaction_date").split(" ")
        sales_order.transaction_date = arr[0]
        sales_order.delivery_date = order_list.get("delivery_date")
        sales_order = add_items_in_order(sales_order, order_list.get("items"), order_list)
        sales_order.status = order_list.get("status")
        sales_order.mode_of_payment = order_list.get("mode_of_payment")
        sales_order.mpesa_no = order_list.get("mpesa_no")
        if order_list.get("coupon_code"):
                coupon_name = frappe.db.get_value("Coupon Code", {"coupon_code": order_list.get("coupon_code")},"name")
                sales_order.coupon_code = coupon_name
        if order_list.get("gift_card_code"):
                sales_order.custom_gift_card_code = order_list.get("gift_card_code")
                sales_order.apply_discount_on="Grand Total"
                sales_order.discount_amount=order_list.get("discount_amount")

        sales_order.disable_rounded_total = 1
        cost_center = order_list.get("cost_center")
        
       
        # Set custom payment status
        if order_list.get("mode_of_payment") == "Card":
            sales_order.custom_payment_status = "Pending"
        else:
            sales_order.custom_payment_status = "Paid"
        
        # Set cost center and warehouse
        sales_order.cost_center = order_list.get("cost_center")
        warehouse = get_warehouse_for_cost_center(order_list.get("cost_center"))
        if warehouse:
            sales_order.set_warehouse = warehouse
        if order_list.get("redeem_loyalty_points") == 1 :
               sales_order.custom_redeem_loyalty_points = 1
               sales_order.loyalty_points = order_list.get("loyalty_points")
               sales_order.loyalty_amount = order_list.get("loyalty_amount")               
               sales_order.custom_redemption_account = order_list.get("loyalty_redemption_account")   
        if order_list.get("loyalty_program") :
               sales_order.custom_loyalty_program = order_list.get("loyalty_program")        
        if order_list.get("pos_opening_shift") :              
               sales_order.custom_pos_shift=order_list.get("pos_opening_shift")

        sales_order.save(ignore_permissions=True)
        sales_order.rounded_total=sales_order.grand_total
        if order_list.get("redeem_loyalty_points") == 1 :
               sales_order.outstanding_amount=sales_order.grand_total-sales_order.loyalty_amount

        sales_order.submit()               
        # if order_list.get("gift_card_code"):
        #         frappe.db.sql("""
        #                 UPDATE `tabSales Order`
        #                 SET `grand_total` = %s,
        #                 `discount_amount`=%s,
        #                 `net_total`=%s
        #                 WHERE name = %s
        #         """, (sales_order.grand_total -float(order_list.get("discount_amount")) ,float(order_list.get("discount_amount")),sales_order.net_total -float(order_list.get("discount_amount")), sales_order.name))           
                  
        create_sales_invoice_from_sales_order(sales_order,order_list.get("gift_card_code"),order_list.get("discount_amount"))

        latest_order = frappe.get_doc('Sales Order', sales_order.name)

        times = [item.get("estimated_time") for item in order_list.get("items")]
        times = [time if time is not None else 0 for time in times]
        max_time = max(times)

        if order_list.get("source") != "WEB":
            kds=frappe.get_doc({
                "doctype": "Kitchen-Kds",
                "order_id": latest_order.get('name'),
                "type": order_list.get("type"),
                "estimated_time": max_time,
                "status": "Open",
                "creation1": now(),
                "custom_order_request": order_list.get('order_request'),
                "source": order_list.get('source'),
                "cost_center": order_list.get("cost_center")
            })
            kds.insert(ignore_permissions=1)


        res['success_key'] = 1
        res['message'] = "success"
        res["sales_order"] = {
            "name": sales_order.name,
            "doc_status": sales_order.docstatus
        }

        if frappe.local.response.get("exc_type"):
            del frappe.local.response["exc_type"]
        
        return res

    except Exception as e:
        if frappe.local.response.get("exc_type"):
            del frappe.local.response["exc_type"]

        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": str(e)
        }


@frappe.whitelist()
def get_sales_order_item_details(order_id=None):
    try:
        if order_id:
                doc = frappe.get_doc("Sales Order", order_id)
                address = frappe.db.sql("""
                SELECT CONCAT(cost_center_name, ", ", custom_address, ", ", custom_location) as address 
                FROM `tabCost Center`
                WHERE name = %s
                """, (doc.cost_center,), as_dict=True)

                item_list = grouping_combo_attr(order_id)
                data = {}
                max_time = []
                for item in doc.items:
                    estimated_time =frappe.db.get_value("Item", {"item_code" : item.item_code}, 'custom_estimated_time')
                    max_time.append(estimated_time)


                data["order_request"] = doc.custom_order_request
                data["item_details"] = item_list
                if address:
                        data['address'] = address[0]['address']
                data["estimated_time"] = max(max_time)
                return data

    except Exception as e:
        if frappe.local.response.get("exc_type"):
            del frappe.local.response["exc_type"]

        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_kitchen_kds(status, cost_center=None):
    try:

        start_datetime = add_to_date(now(), hours=-24)
        end_datetime = now()

        start_datetime_str = str(start_datetime)
        end_datetime_str = str(end_datetime)

        cost_center_condition = ""
        if cost_center:
            cost_center_condition = "AND cost_center = %s"

        all_order = frappe.db.sql(f"""
            SELECT 
                name, 
                order_id, 
                custom_order_request, 
                status, 
                cost_center,                 
                estimated_time, 
                type, 
                CONCAT(creation1, ' ', time) AS creation1, 
                source
            FROM `tabKitchen-Kds`
            WHERE CONCAT(creation1, ' ', time) BETWEEN %s AND %s
            AND status = %s {cost_center_condition}
            ORDER BY CONCAT(creation1, ' ', time) DESC
        """, (start_datetime_str, end_datetime_str, status) + ((cost_center,) if cost_center else ()), as_dict=True)

        for orders in all_order:
            try:
               
                        
                orders['items'] =grouping_combo_attr(orders.order_id)

            except Exception as e:
                return {"message": str(e)}

        # frappe.publish_realtime('realtime_update', message=all_order)

        return all_order

    except Exception as e:
        return {"message": str(e)}


def grouping_combo_attr(order_id):
                query =  """
                                        SELECT 
                                        soi.item_code,
                                        soi.item_name,
                                        soi.custom_ca_id,
                                        soi.rate,
                                        soi.custom_is_combo_item,
                                        soi.custom_is_attribute_item,
                                        soi.custom_parent_item,
                                        soi.qty
                                        FROM 
                                        `tabSales Order Item` soi,`tabSales Order` s
                                        WHERE 
                                        soi.parent=s.name and 
                                        soi.parent = %s
                                        """

                items = frappe.db.sql(query, (order_id,), as_dict=True)
                                
                
                grouped_items = {}

                for item in items:
                        ca_id = item['custom_ca_id']
                        parent_item = item['custom_parent_item']
                        
                        if ca_id not in grouped_items:
                                grouped_items[ca_id] = []

                        if parent_item is None:

                                grouped_items[ca_id].append({
                                "item_code": item["item_code"],
                                "item_name": item["item_name"],
                                "custom_ca_id": item["custom_ca_id"],
                                'price':item['rate'],
                                "custom_is_combo_item": item["custom_is_combo_item"],
                                "custom_is_attribute_item": item["custom_is_attribute_item"],
                                "qty": item["qty"],
                                "child_items": []
                                })
                        
                for item in items:
                        ca_id = item['custom_ca_id']
                        parent_item = item['custom_parent_item']
                        if parent_item is not None:
                                for parent in grouped_items.get(ca_id, []):
                                        if parent["item_code"] == parent_item:
                                                parent["child_items"].append({
                                                "item_code": item["item_code"],
                                                "item_name": item["item_name"],
                                                'price':item['rate'],
                                                "custom_ca_id": item["custom_ca_id"],
                                                "custom_is_combo_item": item["custom_is_combo_item"],
                                                "custom_is_attribute_item": item["custom_is_attribute_item"],
                                                "custom_parent_item": item["custom_parent_item"],
                                                "qty": item["qty"]
                                                })


                output = []

                for items_list in grouped_items.values():
                        output.extend(items_list)
                        
                        
                return output



@frappe.whitelist(methods="POST")
def return_sales_order(sales_invoice):
    try:
        frappe.set_user("Administrator")
        res = frappe._dict()
        # Fetch the sales invoice number
        sales_order_number = sales_invoice.get("sales_order_number")
        sales_invoice_doc = frappe.db.get_value("Sales Invoice Item",
                                                filters={"sales_order": sales_order_number},
                                                fieldname=["parent"])
        if sales_invoice_doc:
            invoice = frappe.get_doc("Sales Invoice", sales_invoice_doc)
            return_order_items = sales_invoice.get("return_items")
            # Update invoice fields for return
            invoice.is_return = 1
            invoice.update_outstanding_for_self = 1
            invoice.return_against = sales_invoice_doc
            invoice.update_billed_amount_in_delivery_note = 1
            invoice.total_qty = -sales_invoice.get("total_qty")
            invoice.mode_of_payment = ''
            invoice.redeem_loyalty_points = 0
            invoice.loyalty_points = 0
            invoice.loyalty_amount = 0
            invoice.loyalty_program = ''
            invoice.loyalty_redemption_account = ''            
            invoice.coupon_code=''
            invoice.discount_amount=-invoice.discount_amount
            returned_items = []
            # Adjust quantities for returned items
            for item in invoice.items:
                if return_order_items.get(item.item_code, 0) > 0:
                    item.qty = -return_order_items[item.item_code]
                    item.stock_qty = -return_order_items[item.item_code]
                    returned_items.append(item)
            invoice.items = returned_items
            invoice.insert(ignore_permissions=1)
            # Update sales order custom status
            frappe.db.sql("""
                UPDATE `tabSales Order`
                SET `custom_return_order_status` = %s
                WHERE name = %s
            """, (sales_invoice.get("return_type"), sales_order_number))
            res["success_key"] = 1
            res["message"] = "Success"
            res['invoice'] = invoice.name
            res['amount'] = invoice.grand_total
            try:
                # Send email to customer with the sales invoice return attached
                send_credit_note_email(invoice)  
            except Exception as e:
                   pass            
            return res
        else:
            res["success_key"] = 0
            res["message"] = "Sales invoice not found for this order."
            res['invoice'] = ""
            res['amount'] = 0
            return res
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "return_sales_order Error")
        return {"success_key": 0, "message": "An unexpected error occurred. Please try again later.", "invoice": "", "amount": 0}



def send_credit_note_email(invoice):
        customer = frappe.get_doc("Customer", invoice.customer)
        contact_doc = frappe.get_doc("Contact", customer.customer_primary_contact)
        email = contact_doc.email_id
        subject = "Credit Note: {}".format(invoice.name)
        message = "Please find attached the Credit Note {}.".format(invoice.name)
        # Use Frappe's PDF generation tool to create the PDF
        pdf_content = frappe.utils.pdf.get_pdf(frappe.render_template(
            'getpos/templates/pages/credit_note_email.html', {"doc": invoice}
        ))
        attachments = [{
            "fname": "Credit_Note_{}.pdf".format(invoice.name.replace(" ", "_")),
            "fcontent": pdf_content
        }]
        frappe.sendmail(
            recipients=email,
            subject=subject,
            message=message,
            attachments=attachments,
            now=True
        )

@frappe.whitelist()
def get_sales_order_list(hub_manager = None, page_no = 1, from_date = None, to_date = nowdate() , mobile_no = None,name=None):
        res= frappe._dict()
        base_url = frappe.db.get_single_value('nbpos Setting', 'base_url')
        filters = {'hub_manager': hub_manager, 'base_url': base_url}
        sales_history_count = frappe.db.get_single_value('nbpos Setting', 'sales_history_count')
        limit = cint(sales_history_count)
        conditions = ""
        if mobile_no:
                conditions += f" and s.contact_mobile like '%{str(mobile_no).strip()}%'"
        if name:
                conditions += f" and s.customer_name like '%{str(name).strip()}%'"
        
        if from_date:
                conditions += " and s.transaction_date between {} and {} order by s.creation desc".format(frappe.db.escape(from_date), frappe.db.escape(to_date))
        else:
                if page_no == 1:
                        row_no = 0
                        conditions += f" order by s.creation desc limit {row_no} , {limit}"
                else:
                        page_no = cint(page_no) - 1
                        row_no = cint(page_no * cint(sales_history_count))
                        conditions += f" order by s.creation desc limit {row_no} , {limit}"
                        
        order_list = frappe.db.sql("""SELECT 
                        s.name, s.transaction_date, TIME_FORMAT(s.transaction_time, '%T') as transaction_time, s.ward, s.customer,s.customer_name, 
                        s.ward, s.hub_manager, s.total , s.total_taxes_and_charges , s.grand_total, s.mode_of_payment, 
                        s.mpesa_no, s.contact_display as contact_name,
                        s.contact_phone, s.contact_mobile, s.contact_email,
                        s.hub_manager, s.creation, s.loyalty_points,s.loyalty_amount,s.discount_amount,
                        s.additional_discount_percentage as discount_percentage,
                        u.full_name as hub_manager_name,
                        if((c.image = null or c.image = ''), null, 
                        if(c.image LIKE 'http%%', c.image, concat({base_url}, c.image))) as image,
                        s.custom_return_order_status as return_order_status,
                        CASE WHEN s.coupon_code = null THEN '' ELSE (select coupon_type from `tabCoupon Code` co where co.name=s.coupon_code) END  as coupon_type,
                        CASE WHEN s.coupon_code = null THEN '' ELSE (select coupon_code from `tabCoupon Code` co where co.name=s.coupon_code) END  as coupon_code,
                        s.custom_gift_card_code as gift_card_code           
                FROM `tabSales Order` s, `tabUser` u, `tabCustomer` c
                WHERE s.hub_manager = u.name and s.customer = c.name 
                        and s.hub_manager = {hub_manager}  and s.docstatus = 1 
                         {conditions}
        """.format(conditions=conditions, hub_manager= frappe.db.escape(hub_manager),
        base_url= frappe.db.escape(base_url)), as_dict= True)
        for item in order_list:
                item_details = frappe.db.sql("""
                        SELECT
                                so.item_code, so.item_name, so.qty,
                                so.uom, so.rate, so.amount,
                                if((i.image = null or i.image = ''), null, 
                                if(i.image LIKE 'http%%', i.image, concat(%s, i.image))) as image
                        FROM 
                                `tabSales Order` s, `tabItem` i, `tabSales Order Item` so
                        WHERE 
                                so.parent = s.name and so.item_code = i.item_code 
                                and so.parent = %s and so.parenttype = 'Sales Order' 
                                and so.associated_item is null
                """, (base_url,item.name), as_dict = True)

                
                associate_items = get_sub_items(item.name)
                new_item_details = []
                if associate_items:
                        for so_item in item_details :
                                so_item['sub_items'] = list(filter( lambda x : x.get("associated_item")== so_item.get("item_code"), associate_items  ) )
                                
                                new_item_details.append(so_item)
                                
                combo_items = get_combo_items(item.name)

                if combo_items:
                        for item_detail in new_item_details :
                                item_detail["combo_items"] = list(filter( lambda x: x.get("parent_item") == item_detail.item_code , combo_items )) 
                                
                item['items'] = new_item_details
                tax_details = frappe.db.sql("""SELECT st.charge_type, st.account_head, st.tax_amount, st.description, st.rate 
                                   FROM `tabSales Order` s, `tabSales Taxes and Charges` st 
                                   WHERE st.parent = %s and st.parent = s.name and st.parenttype = 'Sales Order' """,
                                   (item.name,), as_dict=True)
                item['tax_detail'] = tax_details
        if mobile_no:
                conditions += f" and s.contact_mobile like '%{str(mobile_no).strip()}%'"

                number_of_orders = frappe.db.sql(f"SELECT COUNT(*) FROM `tabSales Order` s WHERE s.hub_manager = {frappe.db.escape(hub_manager)} and s.docstatus = 1 and s.contact_mobile like '%{str(mobile_no).strip()}%'")[0][0]

        else:
                number_of_orders = get_sales_order_count(hub_manager)
                
        if from_date:
                number_of_orders = len(order_list)
                
        

        if len(order_list) == 0 and number_of_orders == 0:
            frappe.clear_messages()
            frappe.local.response["message"] = {
                "success_key":1,
                "message":"no values found for this hub manager "
            }
        else:
            res["success_key"] = 1
            res["message"] = "success"
            res['order_list'] = order_list
            res['number_of_orders'] = number_of_orders
            res['items_perpage']=sales_history_count
            return res

                
def get_sub_items(name):
        base_url = frappe.db.get_single_value('nbpos Setting', 'base_url')
        filters={'name': name ,  'base_url': base_url}
        sub_items = frappe.db.sql("""
                SELECT
                soi.item_code , soi.item_name, soi.qty,soi.uom , soi.rate , 
                soi.amount, soi.associated_item ,
                if((image = NULL or image = ''), "", 
                if(image LIKE 'http%%', image, concat(%(base_url)s, image))) as image
                FROM `tabSales Order` so , `tabSales Order Item` soi
                WHERE so.name = soi.parent and so.name = %(name)s
                """,values=filters ,  as_dict = True)
        if sub_items:
                return sub_items
        else:
                return ""

@frappe.whitelist()
def get_sales_order_count(hub_manager):
        number_of_orders = frappe.db.sql("""
                SELECT 
                        count(s.name)
                FROM `tabSales Order` s, `tabUser` u
                WHERE s.hub_manager = u.name and s.hub_manager = %s
                        and s.docstatus = 1 
                        order by s.creation desc
        """, (hub_manager))[0][0]
        return number_of_orders


@frappe.whitelist()
def review_rating_order():
        review_order = frappe.request.data
        review_order = json.loads(review_order)
        review_order = review_order["review_order"]
        try:
                res = frappe._dict()
                sales_order = frappe.get_doc("Sales Order", review_order.get("name"))
                sales_order.custom_rating = review_order.get("rating")
                sales_order.custom_review = review_order.get("review")
                sales_order.save(ignore_permissions=True)
                sales_order.submit()
                
                res['success_key'] = 1
                res['message'] = "success"
                res["sales_order"] ={
                "name" : sales_order.name,
                "doc_status" : sales_order.docstatus
                }
                if frappe.local.response.get("exc_type"):
                        del frappe.local.response["exc_type"]
                return res

        except Exception as e:
                if frappe.local.response.get("exc_type"):
                        del frappe.local.response["exc_type"]

                frappe.clear_messages()
                frappe.local.response["message"] ={
                "success_key":0,
                "message":e
                        }

@frappe.whitelist()
def update_status(order_status):
        try:
                doc=frappe.get_doc("Kitchen-Kds",{"order_id":order_status.get('name')})
                doc.status= order_status.get('status')
                doc.save(ignore_permissions=True)

                send_order_ready_email(order_status)
                return {"success_key":1, "message": "success"}

        except Exception as e:
                return {"success_key":0, "message": e}
        
def send_order_ready_email(order_status):
        order = frappe.get_doc("Sales Order", order_status.get('name'))
        customer = frappe.get_doc("Customer", order.customer)
        cost_center =order.cost_center
        restaurant_name = frappe.db.get_value("Cost Center", cost_center, "cost_center_name")

        subject = "Your Order is Ready for Pickup"
        message = f"""
        Dear {customer.customer_name}, <br><br>

        Good news! Your order from {restaurant_name} is prepared and ready for pickup. <br><br>

        <b>Order ID</b>: {order.name} <br> <br>

        We look forward to serving you. <br> <br>

        Thank you for choosing {restaurant_name}! <br><br><br>

        Best regards, <br> <br>
        The {restaurant_name} Team<br><br>

        <b>Disclaimer</b>:
        Please note that email is auto generated and the inbox is unmonitored. For any cancellation requests or inquiries regarding your order, kindly contact the business directly.
        """
        frappe.sendmail(
                recipients=customer.email_id,
                subject=subject,
                message=message,
                now=True
        )
    
def get_combo_items(name):
        combo_items = frappe.db.sql(''' Select 
        pi.parent_item,
        pi.item_code , 
        pi.item_name ,
        pi.qty , 
        pi.uom
        from `tabSales Order` so , `tabPacked Item`  pi
        Where 
        so.name = %s and
        so.name = pi.parent
        ''',(name), as_dict = True)
     
        return combo_items






