import frappe
from frappe import _

STANDARD_USERS = ("Guest", "Administrator")
from frappe.utils.pdf import get_pdf
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

def create_sales_invoice_from_sales_order(doc,gift_card_code,discount_amount):
    if (doc.custom_source == "WEB"):
        pass
    else:
        sales_invoice = make_sales_invoice(doc.name)
        sales_invoice.posting_date = doc.transaction_date
        sales_invoice.posting_time = doc.transaction_time
        sales_invoice.due_date = doc.transaction_date        
        sales_invoice.update_stock = 1
        sales_invoice.posa_pos_opening_shift=doc.custom_pos_shift
        if doc.custom_redeem_loyalty_points:
            sales_invoice.redeem_loyalty_points = doc.custom_redeem_loyalty_points
            sales_invoice.loyalty_points = doc.loyalty_points
            sales_invoice.loyalty_amount = doc.loyalty_amount
            sales_invoice.loyalty_program = doc.custom_loyalty_program
            sales_invoice.loyalty_redemption_account = doc.custom_redemption_account
        if doc.coupon_code:
            sales_invoice.coupon_code=doc.coupon_code
        if doc.custom_gift_card_code:
            sales_invoice.discount_amount=doc.discount_amount
            sales_invoice.apply_discount_on="Grand Total"
            sales_invoice.grand_total=sales_invoice.grand_total -float(discount_amount)
        sales_invoice.save(ignore_permissions=1)
        sales_invoice.submit()
        if doc.custom_gift_card_code:
                company_name = frappe.get_doc("Global Defaults").default_company
                company=frappe.get_doc("Company",company_name)             
                journal_entry = frappe.new_doc("Journal Entry")
                journal_entry.voucher_type="Journal Entry"
                journal_entry.company=company.name
                journal_entry.posting_date=frappe.utils.getdate()	
                journal_entry.user_remark="customer redeemed the gift card in partial amount that is for $" + str(discount_amount) + " for the purchase of the good"		
                journal_entry.append(
                        "accounts",
                        {
                        'account': "Gift card Revenue - " + company.abbr,
                        'debit_in_account_currency': float(discount_amount),
                        'credit_in_account_currency': float(0),
                        # 'reference_type':"Sales Invoice",
                        # 'reference_name':sales_invoice.name,
                        'party_type':'Customer',
                        'party':doc.customer
                        })
                journal_entry.append(
                        "accounts",
                        {
                        'account': "Sales - " + company.abbr,
                        'debit_in_account_currency': float(0),
                        'credit_in_account_currency':float(discount_amount),
                        'party_type':'Customer',
                        'party':doc.customer
                })	
                journal_entry.save(ignore_permissions=True)
                journal_entry.submit() 
                gift_card_doc=frappe.db.get_value("Gift Card", {"code": gift_card_code}, ["name", "amount_balance", "amount_used"], as_dict=True)  
                frappe.set_value('Gift Card', gift_card_doc.name, 'amount_balance', gift_card_doc.amount_balance - float(discount_amount))            
                frappe.set_value('Gift Card', gift_card_doc.name, 'amount_used', gift_card_doc.amount_used + float(discount_amount))  
        grand_total=frappe.db.get_value('Sales Invoice', {'name': sales_invoice.name}, 'grand_total')
        if grand_total > 0:
              create_payment_entry(sales_invoice) 
        else:
              frappe.db.sql("""
                        UPDATE `tabSales Invoice`
                        SET `status` = %s                        
                        WHERE name = %s
                """, ("Paid",sales_invoice.name))      
        resend_sales_invoice_email(doc.name)

@frappe.whitelist()
def resend_sales_invoice_email(sales_order):
    res={}
    sales_invoice_doc = frappe.db.get_value("Sales Invoice Item",
                                                filters={"sales_order": sales_order},
                                                fieldname=["parent"])
    if sales_invoice_doc:
        sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_doc)        
        recipient = sales_invoice.contact_email
        # Check if the recipient email is present
        if recipient:
                # Generate PDF content
                pdf_content = get_sales_invoice_pdf(sales_invoice)
                # Prepare the email content
                email_subject = f"Sales Invoice {sales_invoice}"
                email_message = f"Dear {sales_invoice.customer_name},\n\nPlease find attached your sales invoice.\n\nBest regards,\nYour Company Name"
                # Create an attachment
                attachment = {
                        'fname': f"{sales_order}.pdf",
                        'fcontent': pdf_content
                }
                try:
                        # Send the email
                        frappe.sendmail(
                                recipients=[recipient],
                                subject=email_subject,
                                content=email_message,
                                attachments=[attachment],
                                send_email=True
                        )
                        res["success_key"]=1
                        return res
                except Exception as e:
                        res["success_key"]=0
                        res['message'] = "Unable to send mail."    
                        return res
        else:
              res["success_key"]=0
              res['message'] = "Email not found."    
              return res
    else:
          res["success_key"]=0
          res['message'] = "Invoice not found."    
          return res

def get_sales_invoice_pdf(sales_invoice):
    html = frappe.render_template('getpos/templates/pages/sales_invoice_email.html', context={'doc': sales_invoice})
    pdf_content = get_pdf(html)
    return pdf_content

def create_payment_entry(doc):
    if doc.mode_of_payment != 'Credit':
        payment_entry = get_payment_entry("Sales Invoice", doc.name)
        payment_entry.posting_date = doc.posting_date
        payment_entry.mode_of_payment = doc.mode_of_payment
        if doc.mode_of_payment == 'Cash':
                account = frappe.db.get_value('Account', 
                        {
                                'disabled': 0,
                                'account_type': 'Cash',
                                'account_name': 'Cash'
                        },
                        'name')
                payment_entry.paid_to = account
        if doc.mode_of_payment == 'M-Pesa':
                payment_entry.reference_no = doc.mpesa_no
                payment_entry.reference_date = doc.posting_date
        payment_entry.save()
        payment_entry.submit()

@frappe.whitelist(methods="POST")
def create_web_sales_invoice():
    import json
    data = frappe.request.data
    data = json.loads(data)
    data = data["message"]
    try:
        frappe.set_user("Administrator")
        res = frappe._dict()
        if data.get('status') == "F":
                doc = frappe.get_doc("Sales Order", data.get('order_id'))
                total_time=[]
                sales_order_items = frappe.db.get_all('Sales Order Item', filters={'parent': doc.name}, fields=['item_code'])
                for item in sales_order_items:
                        time = frappe.get_value("Item", {"item_code": item.get('item_code')}, 'custom_estimated_time')
                        total_time.append(time)
                max_time = max(total_time)

                sales_invoice = make_sales_invoice(doc.name)
                sales_invoice.posting_date = doc.transaction_date
                sales_invoice.posting_time = doc.transaction_time
                sales_invoice.due_date = data.get('transaction_date')
                sales_invoice.update_stock = 1
                sales_invoice.save(ignore_permissions=1)
                sales_invoice.submit()

                frappe.get_doc({
                    "doctype": "Kitchen-Kds",
                    "order_id": doc.name,
                    "type": "Takeaway",   
                    "estimated_time": max_time, 
                    "status": "Open",
                    "creation1": data.get('transaction_date'),
                    "custom_order_request": doc.custom_order_request,
                    "source": "WEB"
                }).insert(ignore_permissions=1)

                res['success_key'] = 1
                res['message'] = "success"
                res["sales_order"] = {
                    "name": sales_invoice.name,
                    "doc_status": sales_invoice.docstatus
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
