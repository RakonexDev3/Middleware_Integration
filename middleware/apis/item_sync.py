import frappe
import requests


def get_middleware_settings():
    settings = frappe.get_cached_doc("Middleware External Settings")

    if not settings.enable_product_sync:
        return None

    if not settings.endpoint:
        frappe.msgprint("Please configure the Endpoint in Middleware External Settings.")
        return None

    if not settings.get_password("authorization_token"):
        frappe.msgprint("Please configure the Authorization Token in Middleware External Settings.")
        return None

    return settings


def item_created(doc, method):
    if not get_middleware_settings():
        return
    
    frappe.enqueue(
        "middleware.apis.item_sync.sync_item",
        data={
            "item_code": doc.name,
            "event": "create"
        },
        queue="short",
        enqueue_after_commit=True
    )


def item_updated(doc, method):
    if doc.creation == doc.modified:
        return
    
    if not get_middleware_settings():
        return
    
    frappe.enqueue(
        "middleware.apis.item_sync.sync_item",
        data={
            "item_code": doc.name,
            "event": "update"
        },
        queue="short",
        enqueue_after_commit=True
    )


def item_deleted(doc, method):
    if not get_middleware_settings():
        return
    
    frappe.enqueue(
        "middleware.apis.item_sync.sync_item_delete",
        item_code=doc.item_code,
        queue="short",
        enqueue_after_commit=True
    )


def sync_item(data):
    try:
        settings = get_middleware_settings()
        if not settings:
            return
        
        token = settings.get_password("authorization_token")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        item_code = data["item_code"]
        event = data["event"]

        doc = frappe.get_doc("Item", item_code)

        payload = build_payload(doc, event)

        response = requests.post(
            settings.endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

    except Exception:
        frappe.log_error(
            title=f"Item {event.capitalize()} Sync Failed",
            message=f"""
                Status: {response.status_code}
                Response: {response.text}
                {frappe.get_traceback()}
                """
        )


def sync_item_delete(item_code):
    try:
        settings = get_middleware_settings()
        if not settings:
            return
        
        token = settings.get_password("authorization_token")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        payload = {
            "event": "delete",
            "item_code": item_code
        }

        response = requests.post(
            settings.endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

    except Exception:
        frappe.log_error(
            title="Item Delete Sync Failed",
            message=f"""
                Status: {response.status_code}
                Response: {response.text}
                {frappe.get_traceback()}
                """
        )


def build_payload(doc, event):
    return {
        "event": event,
        "item": {
            "SKU": doc.item_code,
            "product_title": doc.item_name,
            "arabic_title": doc.arabic_title,
            "body_html": doc.description,
            "brand": doc.brand,
            "status": "inactive" if doc.disabled else "active",

            "default_uom": doc.stock_uom,

            "selling_price": get_selling_price(doc.item_code),

            "recommended_age": doc.recommended_age,

            "material": doc.material,

            "dimensions": doc.dimensions,

            "product_weight": doc.product_weight,

            "package_dimensions": doc.package_dimensions,
            "package_weight": doc.package_weight,
        }
    }


def get_selling_price(item_code):
    return frappe.db.get_value(
        "Item Price",
        {
            "item_code": item_code,
            "price_list": "Standard Selling"
        },
        "price_list_rate"
    )