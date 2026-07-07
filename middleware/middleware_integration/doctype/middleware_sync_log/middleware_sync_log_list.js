// Copyright (c) 2026, Aravind R and contributors
// For license information, please see license.txt

frappe.listview_settings["Middleware Sync Log"] = {
    onload(listview) {
        listview.page.add_action_item(__("Retry Sync"), async () => {
            const selected = listview.get_checked_items();
            let queued = false;

            for (const row of selected) {
                const r = await frappe.call({
                    method: "middleware.middleware_integration.doctype.middleware_sync_log.middleware_sync_log.retry_sync",
                    args: {
                        log_name: row.name
                    }
                });

                if (r.message && r.message.queued) {
                    queued = true;
                }
            }

            if (queued) {
                frappe.show_alert({
                    message: __("Sync request queued successfully."),
                    indicator: "green"
                });
                listview.refresh();
            } else {
                frappe.msgprint(__("Only pending or failed sync logs can be retried."));
            }
        });
    }
};