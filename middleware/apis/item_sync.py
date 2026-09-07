import frappe
import requests
from frappe.utils import now_datetime
from middleware.utils import get_middleware_settings


def item_created(doc, method):
    settings = get_middleware_settings(
        endpoint="item_sync_endpoint",
        token="item_sync_authorization_token"
    )
    if not settings:
        return
    
    if not doc.enable_product_sync or doc.has_variants:
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
    
    settings = get_middleware_settings(
        endpoint="item_sync_endpoint",
        token="item_sync_authorization_token"
    )
    if not settings:
        return
    
    if not doc.enable_product_sync or doc.has_variants:
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
    settings = get_middleware_settings(
        endpoint="item_sync_endpoint",
        token="item_sync_authorization_token"
    )
    if not settings:
        return

    if not doc.enable_product_sync or doc.has_variants:
        return
    
    frappe.enqueue(
        "middleware.apis.item_sync.sync_item",
        data={
            "item_code": doc.item_code,
            "event": "delete",
            "is_variant": bool(doc.variant_of)
        },
        queue="short",
        enqueue_after_commit=True
    )


def sync_item(data, log_name=None):
    settings = get_middleware_settings(
        endpoint="item_sync_endpoint",
        token="item_sync_authorization_token"
    )
    
    item_code = data["item_code"]
    event = data["event"]

    if log_name:
        log = frappe.get_doc("Middleware Sync Log", log_name)
    else:
        if event == "delete":
            is_variant = data.get("is_variant", False)
        else:
            is_variant = bool(frappe.db.get_value("Item", item_code, "variant_of"))

        log = create_sync_log(item_code, event, is_variant=is_variant)
    
    endpoint = settings.get("item_sync_endpoint")
    token = settings.get_password("item_sync_authorization_token")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    if event == "delete":
        payload = {
            "event": "delete",
            "item": {
                "SKU": item_code,
                "is_variant": bool(log.is_variant)
            }
        }
    else:
        doc = frappe.get_doc("Item", item_code)
        payload = build_payload(doc, event)

    response = None

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        update_sync_log(log, "Success", response=response.text)

    except Exception:
        update_sync_log(log, "Failed", response=response.text if response else frappe.get_traceback())

        frappe.log_error(
            title=f"Item {event.capitalize()} Sync Failed",
            message=f"""
                Status: {response.status_code}
                Response: {response.text}
                {frappe.get_traceback()}
                """
        )


def create_sync_log(item_code, event, is_variant=False):
    log = frappe.get_doc({
        "doctype": "Middleware Sync Log",
        "document_type": "Item",
        "document": item_code,
        "event": event,
        "sync_type": "Single Document",
        "is_variant": is_variant,
        "status": "Pending"
    })

    log.insert(ignore_permissions=True)

    return log


def update_sync_log(log, status, response=None):
    log.status = status
    log.sync_time = now_datetime()

    if response:
        log.response_message = response

    log.save(ignore_permissions=True)


def build_payload(doc, event):
    attributes = []

    if doc.variant_of:
        template = frappe.get_doc("Item", doc.variant_of)

        for row in doc.attributes:
            attributes.append({
                "attribute": row.attribute,
                "value": row.attribute_value
            })
    
    return {
        "event": event,
        "item": {
            "SKU": doc.item_code,
            "is_variant": bool(doc.variant_of),
            "parent_sku": doc.variant_of,
            "parent_title": template.item_name if doc.variant_of else None,
            "parent_body_html": template.description if doc.variant_of else None,

            "product_title": doc.item_name,
            "arabic_title": doc.arabic_title,
            "product_category": doc.item_group,
            "product_body_html": doc.description,
            "brand": doc.brand,
            "status": "inactive" if doc.disabled else "active",

            "default_uom": doc.stock_uom,
            "selling_price": get_selling_price(doc),
            "price_list": doc.active_price_list,
            "recommended_age": doc.recommended_age,
            "material": doc.material,
            "dimensions": doc.dimensions,
            "product_weight": doc.product_weight,
            "package_dimensions": doc.package_dimensions,
            "package_weight": doc.package_weight,
            "installation_type": doc.installation_type,
            "installation_level": doc.installation_level if doc.installation_type else None,
            "attributes": attributes
        }
    }


def get_selling_price(doc):
    return frappe.db.get_value(
        "Item Price",
        {
            "item_code": doc.item_code,
            "price_list": doc.active_price_list
        },
        "price_list_rate"
    )