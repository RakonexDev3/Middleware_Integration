import frappe


def get_middleware_settings(endpoint, token):
    settings = frappe.get_cached_doc("Middleware External Settings")

    if not settings.enable_product_sync:
        return None
    
    if not settings.get(endpoint):
        frappe.msgprint("Please configure the Endpoint in Middleware External Settings.")
        return None
    
    if not settings.get_password(token):
        frappe.msgprint("Please configure the Authorization Token in Middleware External Settings.")
        return None

    return settings