/** @odoo-module **/
import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";
import { user } from "@web/core/user";

export const systemNotificationService = {
    dependencies: ["bus_service", "notification", "orm"],

    async start(env, { bus_service, notification, orm }) {
        const state = reactive({
            notifications: [],
            count: 0,
        });
        const currentUserId = user.userId;
        try {
            const results = await orm.searchRead(
                "system.notification", 
                [['user_id','=',currentUserId]],
                ["id", "message", "res_model", "res_id", "state", "partner_id"],
                { order: "id desc", limit: 10 }
            );
            state.notifications = results;
            state.count = results.filter(n => n.state === 'unread').length;
        } catch (error) {
            console.error("Failed to fetch initial notifications", error);
        }

        bus_service.subscribe("system_notification_channel", (payload) => {
            console.log("PAYLOAD RECEIVED", payload);

            const exists = state.notifications.some(
                (notif) => notif.id === payload.id
            );

            if (!exists) {
                state.notifications.unshift(payload);
                state.count = state.notifications.filter(n => n.state === 'unread').length;
            }

            const closeNotification = notification.add(payload.message, {
                title: "System Notification",
                type: "info",
                sticky: false,
            });

            setTimeout(() => {
                closeNotification();
            }, 3000);
        });

        return state;
    },
};

registry.category("services").add(
    "system_notification_service", 
    systemNotificationService
);
