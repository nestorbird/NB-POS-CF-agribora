import frappe 
from frappe import _
from frappe.utils import cint
STANDARD_USERS = ("Guest", "Administrator")
from frappe.utils.pdf import get_pdf
from frappe.rate_limiter import rate_limit
from frappe.utils.password import get_password_reset_limit
from frappe.utils import (cint,get_formatted_email, nowdate, nowtime, flt)
from datetime import datetime, timedelta, time

@frappe.whitelist()
def coupon_code_details():
    current_date = datetime.now().date()
    def get_details(entity, fields):
        return {field:entity.get(field) for field in fields}
    def fetch_coupon_and_pricing_rule(coupon_code):
        # Fetch details related to the coupon and its associated pricing rule
        coupon = frappe.db.get_value("Coupon Code", {"coupon_code": coupon_code},
                                     ["name", "used", "maximum_use", "valid_from", "valid_upto", "pricing_rule","description"], as_dict=True)
        if not coupon:
            return None, {"status": "error", "message": _("Coupon code does not exist.")}
        pricing_rule = frappe.get_doc("Pricing Rule", coupon.get("pricing_rule"))
        if not pricing_rule:
            return None, {"status": "error", "message": _("Pricing rule associated with coupon not found.")}
        return coupon, pricing_rule
    pricing_rule_fields = [
        # List of fields to fetch from Pricing Rule document
        "name", "title", "apply_on", "price_or_product_discount", "coupon_code_based", "selling", "buying",
        "applicable_for", "customer", "min_qty", "max_qty", "min_amt", "max_amt", "valid_from", "company",
        "currency", "rate_or_discount", "apply_discount_on", "rate", "discount_amount", "discount_percentage",
        "for_price_list", "doctype", "items", "item_groups", "customers", "customer_groups", "territories"
    ]   
    # Fetch all valid coupons based on current date and their respective pricing rules
    coupons = frappe.db.get_all("Coupon Code", filters={"valid_upto": (">=", current_date),"coupon_type": "Promotional"},
                                fields=["name", "coupon_code", "used", "maximum_use", "valid_from", "valid_upto", "pricing_rule","description"])
    valid_coupons = []
    for coupon in coupons:
        pricing_rule = frappe.get_doc("Pricing Rule", coupon.get("pricing_rule"))
        if coupon["description"] :
                coupon["description"]=frappe.utils.strip_html_tags(coupon["description"])
        # Check if the pricing rule is valid, coupon usage is within limit
        if pricing_rule and is_valid_pricing_rule(pricing_rule, current_date) and coupon["used"] < coupon["maximum_use"]:
            valid_coupons.append({
                **get_details(coupon, ["name","coupon_code", "used", "maximum_use", "valid_from", "valid_upto","description"]),
                "pricing_rule": get_details(pricing_rule, pricing_rule_fields)
            })
           
    # Return success status with valid coupons list
    return {"status": "success", "valid_coupons": valid_coupons}
@frappe.whitelist(methods=["POST"])
def validate_coupon_code(coupon_code=None):
    current_date = datetime.now().date()
    def get_details(entity, fields):
        return {field: entity.get(field) for field in fields}
    def fetch_coupon_and_pricing_rule(coupon_code):
        # Fetch details related to the coupon and its associated pricing rule
        coupon = frappe.db.get_value("Coupon Code", {"coupon_code": coupon_code},
                                     ["name", "used", "maximum_use", "valid_from", "valid_upto", "pricing_rule"], as_dict=True)
        if not coupon:
            return None, {"status": "error", "message": _("Coupon code does not exist.")}
        pricing_rule = frappe.get_doc("Pricing Rule", coupon.get("pricing_rule"))
        if not pricing_rule:
            return None, {"status": "error", "message": _("Pricing rule associated with coupon not found.")}
        return coupon, pricing_rule
    pricing_rule_fields = [
        # List of fields to fetch from Pricing Rule document
        "name", "title", "apply_on", "price_or_product_discount", "coupon_code_based", "selling", "buying",
        "applicable_for", "customer", "min_qty", "max_qty", "min_amt", "max_amt", "valid_from", "company",
        "currency", "rate_or_discount", "apply_discount_on", "rate", "discount_amount", "discount_percentage",
        "for_price_list", "doctype", "items", "item_groups", "customers", "customer_groups", "territories"
    ]
    if coupon_code:
        coupon, pricing_rule = fetch_coupon_and_pricing_rule(coupon_code)
        if not coupon:
            return pricing_rule
        # Validate if the pricing rule associated with the coupon is valid
        if not is_valid_pricing_rule(pricing_rule, current_date):
            return {"status": "invalid", "message": _("Associated pricing rule is invalid.")}
        # Check if the coupon has exceeded its maximum usage limit
        if coupon["used"] >= coupon["maximum_use"]:
            return {"status": "invalid", "message": _("Coupon code has reached its maximum use limit.")}
        # Return valid status with coupon and pricing rule details
        return {
            "status": "valid",
            "message": _("Coupon code and associated pricing rule are valid."),
            "coupon": {
                **get_details(coupon, ["name", "used", "maximum_use", "valid_from", "valid_upto"]),
                "pricing_rule": get_details(pricing_rule, pricing_rule_fields)
            }
        }
    # If no coupon code provided, return an error message
    return {"status": "error", "message": _("Coupon code is required.")}

def is_valid_pricing_rule(pricing_rule, current_date):
    def parse_date(date_str):
        return datetime.strptime(date_str, "%Y-%m-%d").date() if isinstance(date_str, str) else date_str
    # Parse valid_from and valid_upto dates from the pricing rule
    rule_valid_from = parse_date(pricing_rule.get("valid_from"))
    rule_valid_upto = parse_date(pricing_rule.get("valid_upto"))
    # Check if the current date falls within the valid range of the pricing rule
    return (not rule_valid_from or current_date >= rule_valid_from) and (not rule_valid_upto or current_date <= rule_valid_upto)
@frappe.whitelist(methods=["POST"])
def validate_gift_card(gift_card):   
        frappe.set_user("Administrator")
        res = frappe._dict()
        current_date = datetime.now().date()
        gift_card_details = frappe.db.get_all("Gift Card", filters={"valid_upto": (">=", current_date),"code": gift_card.get("code"),"customer":gift_card.get("customer")},
                                        fields=["gift_card_name", "discount_amount", "amount_balance", "valid_from", "valid_upto", "description"])
        if gift_card_details:
                if gift_card_details[0].amount_balance > 0:
                        res['success_key'] = 1
                        res['message'] = "success"
                        res['gift_card']=gift_card_details
                else:
                        res['success_key'] = 1
                        res['message'] = "Code is invalid"    
        else:
                res['success_key'] = 1
                res['message'] = "Code is invalid"    
        return res