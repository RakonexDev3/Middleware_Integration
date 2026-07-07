// Copyright (c) 2026, Aravind R and contributors
// For license information, please see license.txt

frappe.ui.form.on("Middleware Sync Log", {
    refresh(frm) {
        if (frm.doc.status != "Success") {
            frm.add_custom_button(__("Retry Sync"), async function () {
                const r = await frappe.call({
                    method: "middleware.middleware_integration.doctype.middleware_sync_log.middleware_sync_log.retry_sync",
                    args: {
                        log_name: frm.doc.name
                    }
                });

                if (r.message && r.message.queued) {
                    frappe.show_alert({
                        message: __("Sync request queued successfully."),
                        indicator: "green"
                    });
                    frm.reload_doc();
                } else {
                    frappe.msgprint(__("Only pending or failed sync logs can be retried."));
                }
            }, __("Actions"));
        }
    }
});