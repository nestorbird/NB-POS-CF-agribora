import frappe
def get_warehouse_for_cost_center(cost_center):
    warehouse = frappe.db.get_value('Warehouse', {'custom_cost_center': cost_center}, 'name')
    return warehouse
