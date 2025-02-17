import frappe
from frappe import _
STANDARD_USERS = ("Guest", "Administrator")
from frappe.auth import check_password
from frappe.rate_limiter import rate_limit
from frappe.utils.password import get_password_reset_limit
from frappe.utils import (get_formatted_email)

@frappe.whitelist( allow_guest=True )
def login(usr, pwd):
    try:
             # Check if the user is already logged in       
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()

        user = frappe.get_doc('User', frappe.session.user)
        
        if user.api_key and user.api_secret:
                user.api_secret = user.get_password('api_secret')
        else:
                api_generate = generate_keys(frappe.session.user)     


        frappe.response["message"] = {
                "success_key":1,
                "message":"success",
                "sid":frappe.session.sid,
                "api_key":user.api_key if user.api_key else api_generate[1],
                "api_secret": user.api_secret if user.api_secret else api_generate[0],
                "username":user.username,
                "email":user.email
        }
    except Exception as e:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Incorrect username or password",
            "error":e
        }
        
        return
    
@frappe.whitelist( allow_guest=True,methods=["GET"] )
def get_user_details(usr,pwd):
    try:
             # Check if the user is already logged in
        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()

        user = frappe.get_doc('User', usr)
        
        if user.api_key and user.api_secret:
                user.api_secret = user.get_password('api_secret')
        else:
                api_generate = generate_keys(usr)     


        frappe.response["message"] = {
                "success_key":1,
                "message":"success",
                "sid":frappe.session.sid,
                "api_key":user.api_key if user.api_key else api_generate[1],
                "api_secret": user.api_secret if user.api_secret else api_generate[0],
                "username":user.username,
                "email":user.email
        }
    except Exception as e:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Incorrect username or password",
            "error":e
        }
        
        return 
    

def generate_keys(user):
    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)

    # if not user_details.api_key:
    api_key = frappe.generate_hash(length=15)
    user_details.api_key = api_key

    user_details.api_secret = api_secret
    user_details.save(ignore_permissions=True)

    if frappe.request.method == "GET":
        frappe.db.commit()
    

    return user_details.get_password("api_secret"), user_details.api_key
       
@frappe.whitelist(allow_guest=True)
@rate_limit(key='user', limit=get_password_reset_limit, seconds = 24*60*60, methods=['POST'])
def forgot_password(user):
        if user=="Administrator":
                return 'not allowed'

        try:
                user = frappe.get_doc("User", user)
                if not user.enabled:
                        return 'disabled'

                user.validate_reset_password()
                user.reset_password(send_email=True)

                return  {
                        "success_key":1,
                        "message":"Password reset instructions have been sent to your email"
                        }
                
        except frappe.DoesNotExistError:
                frappe.clear_messages()
                del frappe.local.response["exc_type"]
                frappe.local.response["message"] = {
                        "success_key":0,
                        "message":"User not found"
                        }
                
@frappe.whitelist(allow_guest=True)
def reset_password( user,send_email=False, password_expired=False):
                from frappe.utils import random_string, get_url

                key = random_string(32)
                

                url = "/update-password?key=" + key
                if password_expired:
                        url = "/update-password?key=" + key + '&password_expired=true'

                link = get_url(url)
                if send_email:
                        user.password_reset_mail(link)
                return link
@frappe.whitelist( allow_guest=True )
def password_reset_mail(user, link):
                user.send_login_mail(("Password Reset"),
                        "password_reset", {"link": link}, now=True)
@frappe.whitelist()
def change_password(usr,new_pwd,old_pwd):
    try:
        user=frappe.get_doc("User",usr)
        
        if check_password(user.name,old_pwd, delete_tracker_cache=False):
            user.new_password = new_pwd
            user.flags.ignore_password_policy = True
            user.save()
            frappe.clear_messages()
            frappe.local.response["message"] = {
                "success_key": 1,
                "message": "Password changed successfully"
            }
            frappe.local.response["http_status_code"] = 200
    except Exception as e:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Please enter valid password"
        }
        frappe.local.response["http_status_code"] = 403  
@frappe.whitelist( allow_guest=True )                
def send_login_mail(user, subject, template, add_args, now=None):
                """send mail with login details"""
                from frappe.utils.user import get_user_fullname
                from frappe.utils import get_url

                created_by = get_user_fullname(frappe.session['user'])
                if created_by == "Guest":
                        created_by = "Administrator"

                args = {
                        'first_name': user.first_name or user.last_name or "user",
                        'user': user.name,
                        'title': subject,
                        'login_url': get_url(),
                        'created_by': created_by
                }

                args.update(add_args)

                sender = frappe.session.user not in STANDARD_USERS and get_formatted_email(frappe.session.user) or None

                frappe.sendmail(recipients=user.email, sender=sender)
                
@frappe.whitelist(methods=["GET"])
def get_user():
    try:
        current_user = frappe.session.user
        user = frappe.get_doc('User', current_user)

        # Assign the "GetPos User" role if the user doesn't already have it
        if not frappe.db.exists("Has Role", {"parent": current_user, "role": "GetPos User"}):
            user.add_roles("GetPos User")
        
        frappe.db.commit()
          
        # Fetch the User doc based on the current user's email/username
        user = frappe.get_doc('User', current_user)
        if not user.api_key:
            user.api_key = frappe.generate_hash()  
            user.api_secret = frappe.generate_hash()
            user.save(ignore_permissions=True) 
            frappe.db.commit()
        frappe.response["message"] = {
            "success_key": 1,
            "message": "success",
            "sid": frappe.session.sid,
            "api_key": user.api_key ,
            "api_secret": user.get_password('api_secret') ,
            "username": user.username,
            "email": user.email
        }
        
        
    except Exception as e:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Error retrieving user",
            "error": str(e)
        }
        return
