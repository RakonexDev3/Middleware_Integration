frappe.listview_settings["Item"] = {
    onload(listview) {
        listview.page.add_action_item(__("Bulk Sync"), async () => {
            const items = listview.get_checked_items().map(d => d.name);

            const r = await frappe.call({
                method: "middleware.apis.bulk_item_sync.bulk_sync_items",
                args: {
                    items: items
                }
            });

            if (r.message && r.message.queued) {
                frappe.show_alert({
                    message: __("Bulk sync request queued successfully."),
                    indicator: "green"
                });
            } else {
                frappe.msgprint(__("All selected items have been synchronized."));
            }
        });
    }
};