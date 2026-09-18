import frappe

@frappe.whitelist()
def installation_item_details(item_code=None):
    if not item_code:
        return {"error": "Item code is required."}
    
    item = frappe.get_value("Item", item_code, ["item_code", "item_name", "stock_uom", "installation_type", "installation_level"], as_dict=True)

    level_time = frappe.get_value("Installation Level", item.installation_level, "estimated_time") if item.installation_level else None

    teams = frappe.get_list("Installation Team", filters={"team_level": item.installation_level})

    return {
        "item_details": {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "stock_uom": item.stock_uom,
            "installation_type": True if item.installation_type == 1 else False,
            "installation_level": item.installation_level,
            "estimated_installation_time": level_time,
        },        
        "teams": [team.name for team in teams]
    }