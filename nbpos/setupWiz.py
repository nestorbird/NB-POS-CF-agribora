import frappe

from nbpos.custom_api.v1.demo_data import upload_logo_and_set


def run_setup_wizard():
    try:
        upload_logo_and_set()
    except Exception as e:
        frappe.log_error(f"Error completing setup wizard: {str(e)}", "Setup Wizard Error")


