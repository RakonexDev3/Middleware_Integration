import json

import frappe

@frappe.whitelist()
def create_sales_order(data=None):
    """Create a Customer if needed, then create a Sales Order.
    """
    if not data:
        data = frappe.local.form_dict

    data = frappe.parse_json(data)

    customer = data.get("customer")
    if not customer:
        frappe.throw("Missing required field: customer")

    if not frappe.db.exists("Customer", customer):
        cust_doc = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": customer,
                "customer_type": "Individual"
            }
        )
        cust_doc.insert(ignore_permissions=True)
        customer = cust_doc.name

    items = data.get("items") or []
    # Ensure items is a list of dicts
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            items = []

    so_doc = frappe.get_doc(
        {
            "doctype": "Sales Order",
            "customer": customer,
            "transaction_date": data.get("transaction_date"),
            "delivery_date": data.get("delivery_date"),
            "items": items,
        }
    )
    so_doc.insert(ignore_permissions=True)

    # frappe.db.commit()

    return {"sales_order": so_doc.name, "customer": customer}
