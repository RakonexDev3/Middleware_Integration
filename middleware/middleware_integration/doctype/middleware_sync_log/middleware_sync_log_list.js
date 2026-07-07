// Copyright (c) 2026, Aravind R and contributors
// For license information, please see license.txt

frappe.listview_settings["Middleware Sync Log"] = {
    onload(listview) {
        listview.page.add_action_item(__("Retry Sync"), async () => {
            const selected = listview.get_checked_items();

            for (const row of selected) {
                await frappe.call({
                    method: "middleware.middleware_integration.doctype.middleware_sync_log.middleware_sync_log.retry_sync",
                    args: {
                        log_name: row.name
                    }
                });
            }

            frappe.show_alert(__("Sync request queued successfully."));
            listview.refresh();
        });
    }
};