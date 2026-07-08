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

    if log.status == "Success":
        return {"queued": False}

    log.status = "Pending"
    log.retry_count = (log.retry_count or 0) + 1
    log.sync_time = now_datetime()
    log.response_message = ""
    log.save(ignore_permissions=True)

    if log.sync_method == "Bulk Import":
        items = [row.document for row in log.documents if row.document]

        frappe.enqueue(
            "middleware.apis.bulk_item_sync.process_bulk_sync",
            items=items,
            log_name=log.name,
            queue="long",
            enqueue_after_commit=True
        )
    elif log.event == "delete":
        frappe.enqueue(
            "middleware.apis.item_sync.sync_item_delete",
            item_code=log.document,
            log_name=log.name,
            queue="short",
            enqueue_after_commit=True
        )
    else:
        frappe.enqueue(
            "middleware.apis.item_sync.sync_item",
            data={
                "item_code": log.document,
                "event": log.event
            },
            log_name=log.name,
            queue="short",
            enqueue_after_commit=True
        )

    return {"queued": True}