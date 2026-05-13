/** @odoo-module **/
import { registry } from "@web/core/registry";
 
const systrayRegistry = registry.category("systray");
 
if (systrayRegistry.contains("mail.messaging_menu")) {
    systrayRegistry.remove("mail.messaging_menu");
}