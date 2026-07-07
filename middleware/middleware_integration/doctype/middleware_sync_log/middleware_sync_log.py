# Copyright (c) 2026, Aravind R and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class MiddlewareSyncLog(Document):
	pass


@frappe.whitelist()
def retry_sync(log_name):
    log = frappe.get_doc("Middleware Sync Log", log_name)

    log.status = "Pending"
    log.retry_count = (log.retry_count or 0) + 1
    log.sync_time = now_datetime()
    log.response_message = ""
    log.error_message = ""
    log.save(ignore_permissions=True)

    if log.event == "delete":
        frappe.enqueue(
            "middleware.apis.item_sync.sync_item_delete",
            item_code=log.item_code,
            log_name=log.name,
            queue="short",
            enqueue_after_commit=True
        )
    else:
        frappe.enqueue(
            "middleware.apis.item_sync.sync_item",
            data={
                "item_code": log.item_code,
                "event": log.event
            },
            log_name=log.name,
            queue="short",
            enqueue_after_commit=True
        )

    frappe.msgprint("Sync request queued successfully.")