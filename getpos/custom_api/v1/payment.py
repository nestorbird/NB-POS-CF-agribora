import requests
import frappe
import json
from frappe import _
import json
STANDARD_USERS = ("Guest", "Administrator")
@frappe.whitelist(methods="POST")
def payment_request(payment_list={}):
        try:
                auth_url = f'{payment_list.get("auth_token_url")}/connect/token'
                post_data = {
                "grant_type": "client_credentials",
                "client_id": payment_list.get("client_id"),
                "client_secret":payment_list.get("client_secret")
                }
                response = requests.post(auth_url, data=post_data)
                o_auth_authentication_response = response.json()

                api_client = requests.Session()
                base_address = payment_list.get("base_payment_url")
                api = "/checkout/v2/isv/orders?merchantid=" 
                merchantId=  payment_list.get("merchant_id")            
                api_client.headers.update({
                "Accept": "application/json",
                "Authorization": f"Bearer {o_auth_authentication_response['access_token']}"
                })


                customer = {
                        "Email":  payment_list.get("customer_email"),
                        "FullName": payment_list.get("customer_name"),
                        "Phone": payment_list.get("customer_phone"),
                        "CountryCode":  payment_list.get("country_code"),
                        "RequestLang":  payment_list.get("request_lang")
                }
                isvamount= payment_list.get("amount") * payment_list.get("isv_percentage") / 100
                request = {
                        "Amount": payment_list.get("amount"),
                        "CustomerTrns": payment_list.get("customer_trans"),
                        "Customer": customer,
                        "PaymentTimeout": 300,
                        "Preauth": False,
                        "AllowRecurring": False,
                        "MaxInstallments": 12,
                        "PaymentNotification": True,
                        "TipAmount": 0,
                        "DisableExactAmount": False,
                        "DisableWallet": True,
                        "SourceCode": payment_list.get("source_code"),
                        "isvamount": isvamount
                }
                post_request_data = json.dumps(request)
                content_data = post_request_data.encode('utf-8')
                headers = {'Content-Type': 'application/json'}

                api_response = api_client.post(f"{base_address}{api}{merchantId}", data=content_data, headers=headers)

                viva_wallet_order_response = api_response.json()
                
                if api_response.status_code == 200:
                        # post_process_payment_request['Order']['OrderCode'] = viva_wallet_order_response['OrderCode']
                        # await _order_service.update_order_async(post_process_payment_request['Order'])
                        redirect_url = f'{payment_list.get("checkout_url")}/web/checkout?ref={viva_wallet_order_response["orderCode"]}'
                return redirect_url
        except Exception as e:
                if frappe.local.response.get("exc_type"):
                        del frappe.local.response["exc_type"]

                frappe.clear_messages()
                
                frappe.local.response["message"] ={
                "success_key":0,
                "message":e
                        }

@frappe.whitelist()
def transaction_status(payment_list={}, transaction_id=None, merchant_id=None):
    try:
        auth_url = f'{payment_list.get("auth_token_url")}/connect/token'
        post_data = {
            "grant_type": "client_credentials",
            "client_id": payment_list.get("client_id"),
            "client_secret": payment_list.get("client_secret")
        }
        
        response = requests.post(auth_url, data=post_data)
        response.raise_for_status() 
        o_auth_authentication_response = response.json()
        api_client = requests.Session()
        base_address = payment_list.get("base_payment_url")
        api_client.headers.update({
            "Accept": "application/json",
            "Authorization": f"Bearer {o_auth_authentication_response['access_token']}"
        })

        api_url = f"{base_address}/checkout/v2/isv/transactions/{transaction_id}?merchantId={merchant_id}"
        
        api_response = api_client.get(api_url)

        if api_response.status_code == 200:
            transaction_response = api_response.json()
            return transaction_response
        else:
            return {
                "success_key": 0,
                "message": f"Failed to retrieve transaction status. Status code: {api_response.status_code}, Response: {api_response.text}"
            }

    except Exception as e:
        return {
            "success_key": 0,
            "message": str(e)
        }


@frappe.whitelist()
def update_payment_status(update_paymentstatus):
        try:
                frappe.db.set_value("Sales Order", {"name":update_paymentstatus.get('order_id')}, {'custom_payment_status': update_paymentstatus.get('paymentstatus')
                })

                return {"success_key":1, "message": "success"}

        except Exception as e:
                return {"success_key":0, "message": e}
