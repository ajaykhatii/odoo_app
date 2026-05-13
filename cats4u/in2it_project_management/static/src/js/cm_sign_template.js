/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { SignTemplateControlPanel } from "@sign/backend_components/sign_template/sign_template_control_panel";

patch(SignTemplateControlPanel.prototype, {

    setup() {
        super.setup();
        const parent = this.__owl__.parent;
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.onSendClickMail = this.onSendClickMail.bind(this);
    },

    async onSendClickMail() {
        const parent = this.__owl__.parent;
        const params = parent?.props?.action?.params
        const attachment_id = this.props.signTemplate.attachment_id[0]
        const templateId = this.props.signTemplate.id;

        try {
            await this.orm.call(
                "sign.template",
                "send_custom_email",
                [[templateId], attachment_id, params]
            );
            await this.showWizardPopup("Request sent successfully", "Confirmation", params);
        } catch (error) {
            let message = "At least one signer is required or mail delivery failed.";
            if (error?.data?.message) {
                message = error.data.message;
            }
            await this.showWizardPopup(message, "Failed");
        }
    },

    async showWizardPopup(message, title, params) {
        const wizardIds = await this.orm.create("digital.evidence.confirm", [{
            name: message,
        }]);
        const wizardId = wizardIds[0];
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: "digital.evidence.confirm",
            res_id: wizardId,
            views: [[false, "form"]],
            target: "new",
            context: {'params': params},
        });
    }
});