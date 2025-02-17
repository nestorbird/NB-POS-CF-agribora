import frappe
import json
from frappe import _
import requests
from getpos.custom_api.v1.item import get_item_list, get_item_stock_balance
from getpos.controllers import frappe_response,handle_exception
from erpnext.accounts.utils import get_balance_on

@frappe.whitelist()
def get_customer_list_by_hubmanager(hub_manager, last_sync = None):
        res = frappe._dict()
        base_url = frappe.db.get_single_value('nbpos Setting', 'base_url')
        filters = {'hub_manager': hub_manager, "base_url": base_url}
        conditions = "hub_manager = %(hub_manager)s "
        if last_sync:
                filters['last_sync'] = last_sync
                conditions += "and modified >= %(last_sync)s"
        customer_list = frappe.db.sql("""
                SELECT
                        customer_name, email_id, mobile_no,
                        ward, ward_name, name, creation,
                        modified,disabled,
                        if((image = null or image = ''), null, 
                        if(image LIKE 'http%%', image, concat(%(base_url)s, image))) as image ,loyalty_program
                FROM `tabCustomer`
                WHERE {conditions}
                """.format(conditions=conditions), values=filters, as_dict=1)
        if len(customer_list) == 0:
                frappe.clear_messages()
                frappe.local.response["message"] = {
                        "success_key":1,
                        "message":"No values found for this hub manager"
                        }
        else:
                res["success_key"] = 1
                res["message"] = "success"
                res["customer_list"] = customer_list          
                return res 

# Not using for Mobile App
@frappe.whitelist()
def get_item_list_by_hubmanager(hub_manager, last_sync = None):
        res = frappe._dict()
        item_list_based_stock_sync = []
        if last_sync:
                arr =last_sync.split(" ")
                last_sync_date = arr[0]
                if len(arr) < 2:
                        last_sync_time = '00:00:00'
                else:
                        last_sync_time = arr[1]
        base_url = frappe.db.get_single_value('nbpos Setting', 'base_url')
        filters = {'hub_manager': hub_manager, "base_url": base_url}
        conditions = "h.hub_manager = %(hub_manager)s "
        item_list = get_item_list(filters, conditions)
        for item in item_list:
                if last_sync:
                        stock_detail = get_item_stock_balance(hub_manager, item.item_code, last_sync_date, last_sync_time)
                        if stock_detail:
                                item_list_based_stock_sync.append(item)
                else:
                        stock_detail = get_item_stock_balance(hub_manager, item.item_code)
                        item.available_qty = stock_detail.get("available_qty")
                        item.stock_modified = str(stock_detail.get("posting_date"))+" "+str(stock_detail.get("posting_time"))
        if last_sync:
                filters['last_sync'] = last_sync
                conditions += "and (i.modified >= %(last_sync)s or p.modified >= %(last_sync)s)"
                item_list_syn_based = get_item_list(filters, conditions)
                for i in item_list_based_stock_sync:
                        if i in item_list_syn_based:
                                item_list_syn_based.remove(i)
                item_list = item_list_based_stock_sync + item_list_syn_based
                for item in item_list:
                        stock_detail = get_item_stock_balance(hub_manager, item.item_code)
                        item.available_qty = stock_detail.get("available_qty")
                        item.stock_modified = str(stock_detail.get("posting_date"))+" "+str(stock_detail.get("posting_time"))
                if len(item_list) == 0:
                        frappe.clear_messages()
                        frappe.local.response["message"] = {
                                "success_key":1,
                                "message":"No values found for this hub manager"
                        }
                else:
                        res["success_key"] = 1
                        res["message"] = "success"
                        res["item_list"] = item_list 
                        return res        
        else:
                if len(item_list) == 0:
                        frappe.clear_messages()
                        frappe.local.response["message"] = {
                                "success_key":1,
                                "message":"No values found for this hub manager"
                        }
                else:
                        res["success_key"] = 1
                        res["message"] = "success"
                        res["item_list"] = item_list
                        return res 
@frappe.whitelist()
def get_details_by_hubmanager(hub_manager):
    try:
        res = frappe._dict()
        base_url = frappe.db.get_single_value('nbpos Setting', 'base_url')
        filters = {'hub_manager': hub_manager, "base_url": base_url}
        currency = frappe.get_doc("Global Defaults").default_currency
        currency_symbol=frappe.get_doc("Currency",currency).symbol
        conditions = "email = %(hub_manager)s "
        hub_manager_detail = frappe.db.sql("""
                SELECT
                        u.name, u.full_name,
                        u.email , if(u.mobile_no,u.mobile_no,'') as mobile_no,
                        if(u.user_image, if(u.user_image LIKE 'http%%', u.user_image, concat(%(base_url)s, u.user_image)), '') as image
                FROM `tabUser` u
                WHERE
                {conditions}
                """.format(conditions=conditions), values=filters, as_dict=1)
        cash_balance = get_balance(hub_manager)
        last_txn_date = get_last_transaction_date(hub_manager)
       
        res["success_key"] = 1
        res["message"] = "success"
        res["name"] = hub_manager_detail[0]["name"]
        res["full_name"] = hub_manager_detail[0]["full_name"]
        res["email"] = hub_manager_detail[0]["email"]
        res["mobile_no"] = hub_manager_detail[0]["mobile_no"]
        res["hub_manager"] = hub_manager_detail[0]["name"]
        res["series"] = ""
        res["image"] = hub_manager_detail[0]["image"]
        res["app_currency"] = currency_symbol
        res["balance"] = cash_balance
        res["last_transaction_date"] =  last_txn_date if last_txn_date else ''
        res["wards"] = []
   
        return res
    except Exception as e:
        frappe.clear_messages()
        frappe.local.response["message"] = {
                "success_key":0,
                "message":"No values found for this hub manager"
        }



@frappe.whitelist()
def get_balance(hub_manager):
        account = frappe.db.get_value('Account', {'hub_manager': hub_manager}, 'name')
        account_balance = get_balance_on(account)
        return account_balance if account_balance else 0.0

@frappe.whitelist()
def get_last_transaction_date(hub_manager):
        account = frappe.db.get_value('Account', {'hub_manager': hub_manager, 'disabled': 0}, 'name')
        transaction_date = frappe.db.get_list("GL Entry",
                        filters={
                                'account': account,
                                'voucher_type': ["!=",'Period Closing Voucher'],
                                'is_cancelled': 0
                        },
                        fields= ['posting_date'],
                        order_by = "posting_date desc",
                        as_list = 1
        )
        if transaction_date:
                transaction_date = transaction_date[0][0]
        else:
                transaction_date = None
        return transaction_date


