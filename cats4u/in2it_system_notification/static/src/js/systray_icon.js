/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useDiscussSystray } from "@mail/utils/common/hooks";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";


export class SystrayIcon extends Component {
    static components = { Dropdown, DropdownItem };
    static template = "my_module.SystrayIcon";

    setup() {
        this.systemService = useState(
            this.env.services.system_notification_service
        );
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.discussSystray = useDiscussSystray();


        // Required in Odoo 18 for Dropdown
        this.dropdown = useDropdownState();
    }

    async openNotification(notif) {
        // Close dropdown (Odoo 18 standard behavior)
        this.dropdown.close();

        const { res_model, res_id } = notif;

        // Mark as read
        await this._markNotificationAsRead(notif);

        if (res_model && res_id) {
            const recordExists = await this._checkRecordExistence(
                res_model,
                res_id
            );

            if (recordExists) {
                await this.action.doAction({
                    type: "ir.actions.act_window",
                    name: "Notification Channel",
                    res_model: res_model,
                    res_id: res_id,
                    views: [[false, "form"]],
                    target: "current",
                }, { clearBreadcrumbs: true });
            } else {
                const closeError = this.notification.add(
                    `The linked record (ID: ${res_id}) in ${res_model} no longer exists.`,
                    {
                        title: "Record Not Found",
                        type: "danger",
                        sticky: false,
                    }
                );

                setTimeout(() => {
                    closeError();
                }, 3000);

                console.error(
                    `Record with res_model: ${res_model} and res_id: ${res_id} does not exist.`
                );
            }
        } else {
            await this.action.doAction({
                type: "ir.actions.act_window",
                name: "System Notification",
                res_model: "system.notification",
                res_id: notif.id,
                views: [[false, "form"]],
                target: "current",
            }, { clearBreadcrumbs: true });
        }
    }

    async _checkRecordExistence(res_model, res_id) {
        try {
            const record = await this.orm.searchRead(
                res_model,
                [["id", "=", res_id]],
                ["id"]
            );
            return record.length > 0;
        } catch (error) {
            console.error("Error checking record existence:", error);
            return false;
        }
    }

    async _markNotificationAsRead(notif) {
        await this.orm.write("system.notification", [notif.id], {
            state: "read",
        });

        const index = this.systemService.notifications.findIndex(
            (n) => n.id === notif.id
        );

        if (index !== -1) {
            const existing = this.systemService.notifications[index];
    
            if (existing.state !== "read") {
                existing.state = "read";
                this.systemService.count -= 1;
            }
        }
    }

    async deleteNotification(ev, notif) {
        ev.stopPropagation();

        try {
            await this.orm.unlink("system.notification", [notif.id]);

            const index = this.systemService.notifications.findIndex(
                (n) => n.id === notif.id
            );

            if (index !== -1) {
                this.systemService.notifications.splice(index, 1);
                this.systemService.count =
                    this.systemService.notifications.filter(n => n.state === 'unread').length;
            }
        } catch (error) {
            console.error("Failed to delete notification", error);
        }
    }
}

export const systrayItem = { Component: SystrayIcon };

registry
    .category("systray")
    .add("SystemNotificationSystray", systrayItem, { sequence: 10 });
