from __future__ import unicode_literals
import frappe,json
from frappe import _
from frappe.model.document import Document
from frappe.utils import comma_or, nowdate, getdate, flt

@frappe.whitelist()
def get_shift_transaction(pos_opening_shift):
    data = {}

    pos_opening_shift_doc = frappe.get_doc("POS Opening Shift", pos_opening_shift)
    amt = sum(i.get('amount') for i in pos_opening_shift_doc.balance_details)

    sales_orders = frappe.get_all(
        "Sales Order",
        filters={
            "custom_pos_shift": pos_opening_shift,
            "docstatus": 1
        },
        fields=["name", "customer", "grand_total", "status"]
    )

    customers = {order.customer for order in sales_orders}
    customer_first_order_dates = frappe.get_all(
        "Sales Order",
        filters={
            "customer": ["in", list(customers)],
            "docstatus": 1
        },
        fields=["customer", "min(creation) as first_order_date"],
        group_by="customer"
    )
    
    customer_first_order_dates = {entry.customer: entry.first_order_date for entry in customer_first_order_dates}

    old_customers = set()
    new_customers = set()
    sales_order_amount = 0
    return_order_amount = 0
    num_transactions = 0
    cash_collected = 0

    for order in sales_orders:
        amount = order.grand_total

        if order.status == "Return":
            return_order_amount += amount
        else:
            sales_order_amount += amount

        num_transactions += 1
        cash_collected += amount

        # Check if the customer is new or old
        if customer_first_order_dates[order.customer] == order.creation:
            new_customers.add(order.customer)
        else:
            old_customers.add(order.customer)

    data["opening_amount"] = amt
    data["old_customers"] = list(old_customers)
    data["new_customers"] = list(new_customers)
    data["sales_order_amount"] = sales_order_amount
    data["return_order_amount"] = return_order_amount
    data["num_transactions"] = num_transactions
    data["cash_collected"] = cash_collected

    return data



@frappe.whitelist(methods=["GET"])
def get_opening_data():
    frappe.set_user("Administrator")
    data = {}
    data["companys"] = frappe.get_list("Company", limit_page_length=0, order_by="name")
    data["pos_profiles_data"] = frappe.get_list(
        "POS Profile",
        filters={"disabled": 0},
        fields=["name", "company"],
        limit_page_length=0,
        order_by="name",
    )

    pos_profiles_list = []
    for i in data["pos_profiles_data"]:
        pos_profiles_list.append(i.name)

    payment_method_table = (
        "POS Payment Method" if get_version() == 13 else "Sales Invoice Payment"
    )
    data["payments_method"] = frappe.get_list(
        payment_method_table,
        filters={"parent": ["in", pos_profiles_list]},
        fields=["*"],
        limit_page_length=0,
        order_by="parent",
        ignore_permissions=True
    )

    return data


def get_version():
    branch_name = get_app_branch("erpnext")
    if "12" in branch_name:
        return 12
    elif "13" in branch_name:
        return 13
    else:
        return 13

def get_app_branch(app):
    """Returns branch of an app"""
    import subprocess

    try:
        branch = subprocess.check_output(
            "cd ../apps/{0} && git rev-parse --abbrev-ref HEAD".format(app), shell=True
        )
        branch = branch.decode("utf-8")
        branch = branch.strip()
        return branch
    except Exception:
        return ""
    
@frappe.whitelist()
def check_opening_shift(user):
    open_vouchers = frappe.db.get_all(
        "POS Opening Shift",
        filters={
            "user": user,
            "pos_closing_shift": ["in", ["", None]],
            "docstatus": 1,
            "status": "Open",
        },
        fields=["name", "pos_profile"],
        order_by="period_start_date desc",
    )
    data = ""
    if len(open_vouchers) > 0:
        data = {}
        data["pos_opening_shift"] = frappe.get_doc(
            "POS Opening Shift", open_vouchers[0]["name"]
        )
        update_opening_shift_data(data, open_vouchers[0]["pos_profile"])
    return data


def update_opening_shift_data(data, pos_profile):
    data["pos_profile"] = frappe.get_doc("POS Profile", pos_profile)
    data["company"] = frappe.get_doc("Company", data["pos_profile"].company)
    allow_negative_stock = frappe.get_value(
        "Stock Settings", None, "allow_negative_stock"
    )
    data["stock_settings"] = {}
    data["stock_settings"].update({"allow_negative_stock": allow_negative_stock})


@frappe.whitelist()
def create_opening_voucher(pos_profile, company, balance_details):
    if isinstance(balance_details, str):
        balance_details = json.loads(balance_details)

    new_pos_opening = frappe.get_doc(
        {
            "doctype": "POS Opening Shift",
            "period_start_date": frappe.utils.get_datetime(),
            "posting_date": frappe.utils.getdate(),
            "user": frappe.session.user,
            "pos_profile": pos_profile,
            "company": company,
            "docstatus": 1,
        }
    )
    new_pos_opening.set("balance_details", balance_details)
    new_pos_opening.insert(ignore_permissions=True)

    data = {}
    data["pos_opening_shift"] = new_pos_opening.as_dict()
    update_opening_shift_data(data, new_pos_opening.pos_profile)
    return data


class POSClosingShift(Document):
    def validate(self):
        user = frappe.get_all('POS Closing Shift',
                              filters={'user': self.user, 'docstatus': 1},
                              or_filters={
                                  'period_start_date': ('between', [self.period_start_date, self.period_end_date]),
                                  'period_end_date': ('between', [self.period_start_date, self.period_end_date])
                              })

        if user:
            frappe.throw(_("POS Closing Shift {} against {} between selected period"
                           .format(frappe.bold("already exists"), frappe.bold(self.user))), title=_("Invalid Period"))

        if frappe.db.get_value("POS Opening Shift", self.pos_opening_shift, "status") != "Open":
            frappe.throw(_("Selected POS Opening Shift should be open."), title=_(
                "Invalid Opening Entry"))
        self.update_payment_reconciliation()
    
    def update_payment_reconciliation(self):
        # update the difference values in Payment Reconciliation child table
        # get default precision for site
        precision = frappe.get_cached_value('System Settings', None, 'currency_precision') or 3
        for d in self.payment_reconciliation:
            d.difference = flt(d.opening_amount, precision) + flt(d.closing_amount, precision) - flt(d.expected_amount, precision)

    def on_submit(self):
        opening_entry = frappe.get_doc(
            "POS Opening Shift", self.pos_opening_shift)
        opening_entry.pos_closing_shift = self.name
        opening_entry.set_status()
        # self.delete_draft_invoices()
        opening_entry.save()

    def delete_draft_invoices(self):
        if frappe.get_value("POS Profile", self.pos_profile, "posa_allow_delete"):
            data = frappe.db.sql("""
                select
                    name
                from
                    `tabSales Invoice`
                where
                    docstatus = 0 and posa_is_printed = 0 and posa_pos_opening_shift = %s
                """, (self.pos_opening_shift), as_dict=1)

            for invoice in data:
                frappe.delete_doc("Sales Invoice", invoice.name, force=1)

    def get_payment_reconciliation_details(self):
        currency = frappe.get_cached_value(
            'Company', self.company,  "default_currency")
        return frappe.render_template("getpos/getpos/doctype/pos_closing_shift/closing_shift_details.html",
                                      {"data": self, "currency": currency})


@frappe.whitelist()
def get_cashiers(doctype, txt, searchfield, start, page_len, filters):
    cashiers_list = frappe.get_all(
        "POS Profile User", filters=filters, fields=['user'])
    return [c['user'] for c in cashiers_list]


@frappe.whitelist()
def get_pos_invoices(pos_opening_shift):
    submit_printed_invoices(pos_opening_shift)
    data = frappe.db.sql("""
	select
		name
	from
		`tabSales Invoice`
	where
		docstatus = 1 and posa_pos_opening_shift = %s
	""", (pos_opening_shift), as_dict=1)

    data = [frappe.get_doc("Sales Invoice", d.name).as_dict() for d in data]

    return data


@frappe.whitelist()
def make_closing_shift_from_opening(opening_shift):
    if isinstance(opening_shift, str):
        opening_shift = json.loads(opening_shift)
    submit_printed_invoices(opening_shift.get("name"))
    closing_shift = frappe.new_doc("POS Closing Shift")
    closing_shift.pos_opening_shift = opening_shift.get("name")
    closing_shift.period_start_date = opening_shift.get("period_start_date")
    closing_shift.period_end_date = frappe.utils.get_datetime()
    closing_shift.pos_profile = opening_shift.get("pos_profile")
    closing_shift.user = opening_shift.get("user")
    closing_shift.company = opening_shift.get("company")
    closing_shift.grand_total = 0
    closing_shift.net_total = 0
    closing_shift.total_quantity = 0

    invoices = get_pos_invoices(opening_shift.get("name"))

    pos_transactions = []
    taxes = []
    payments = []
    for detail in opening_shift.get("balance_details"):
        payments.append(frappe._dict({
            'mode_of_payment': detail.get("mode_of_payment"),
            'opening_amount': detail.get("amount") or 0,
            'expected_amount': detail.get("amount") or 0
        }))

    for d in invoices:
        pos_transactions.append(frappe._dict({
            'sales_invoice': d.name,
            'posting_date': d.posting_date,
            'grand_total': d.grand_total,
            'customer': d.customer
        }))
        closing_shift.grand_total += flt(d.grand_total)
        closing_shift.net_total += flt(d.net_total)
        closing_shift.total_quantity += flt(d.total_qty)

        for t in d.taxes:
            existing_tax = [tx for tx in taxes if tx.account_head ==
                            t.account_head and tx.rate == t.rate]
            if existing_tax:
                existing_tax[0].amount += flt(t.tax_amount)
            else:
                taxes.append(frappe._dict({
                    'account_head': t.account_head,
                    'rate': t.rate,
                    'amount': t.tax_amount
                }))

        for p in d.payments:
            existing_pay = [
                pay for pay in payments if pay.mode_of_payment == p.mode_of_payment]
            if existing_pay:
                cash_mode_of_payment = frappe.get_value(
                    "POS Profile", opening_shift.get("pos_profile"), "posa_cash_mode_of_payment")
                if not cash_mode_of_payment:
                    cash_mode_of_payment = "Cash"
                if existing_pay[0].mode_of_payment == cash_mode_of_payment:
                    amount = p.amount - d.change_amount
                else:
                    amount = p.amount
                existing_pay[0].expected_amount += flt(amount)
            else:
                payments.append(frappe._dict({
                    'mode_of_payment': p.mode_of_payment,
                    'opening_amount': 0,
                    'expected_amount': p.amount
                }))

    closing_shift.set("pos_transactions", pos_transactions)
    closing_shift.set("payment_reconciliation", payments)
    closing_shift.set("taxes", taxes)

    return closing_shift


@frappe.whitelist()
def submit_closing_shift(closing_shift):
    if isinstance(closing_shift, str):
        closing_shift = json.loads(closing_shift)
    closing_shift_doc = frappe.get_doc(closing_shift)
    closing_shift_doc.flags.ignore_permissions = True
    closing_shift_doc.save()
    closing_shift_doc.submit()
    return closing_shift_doc.name


def submit_printed_invoices(pos_opening_shift):
    invoices_list = frappe.get_all("Sales Invoice", filters={
        "posa_pos_opening_shift": pos_opening_shift,
        "docstatus": 0,
        "posa_is_printed": 1
    })
    for invoice in invoices_list:
        invoice_doc = frappe.get_doc("Sales Invoice", invoice.name)
        invoice_doc.submit()
class OverAllowanceError(frappe.ValidationError): pass

def validate_status(status, options):
	if status not in options:
		frappe.throw(_("Status must be one of {0}").format(comma_or(options)))

status_map = {
	"POS Opening Shift": [
		["Draft", None],
		["Open", "eval:self.docstatus == 1 and not self.pos_closing_shift"],
		["Closed", "eval:self.docstatus == 1 and self.pos_closing_shift"],
		["Cancelled", "eval:self.docstatus == 2"],
	]
}

class StatusUpdater(Document):

	def set_status(self, update=False, status=None, update_modified=True):
		if self.is_new():
			if self.get('amended_from'):
				self.status = 'Draft'
			return

		if self.doctype in status_map:
			_status = self.status
			if status and update:
				self.db_set("status", status)

			sl = status_map[self.doctype][:]
			sl.reverse()
			for s in sl:
				if not s[1]:
					self.status = s[0]
					break
				elif s[1].startswith("eval:"):
					if frappe.safe_eval(s[1][5:], None, { "self": self.as_dict(), "getdate": getdate,
							"nowdate": nowdate, "get_value": frappe.db.get_value }):
						self.status = s[0]
						break
				elif getattr(self, s[1])():
					self.status = s[0]
					break

			if self.status != _status and self.status not in ("Cancelled", "Partially Ordered",
																"Ordered", "Issued", "Transferred"):
				self.add_comment("Label", _(self.status))

			if update:
				self.db_set('status', self.status, update_modified = update_modified)
