/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MailComposerAttachmentList } from "@mail/core/web/mail_composer_attachment_list";
import {
    Many2ManyBinaryField,
} from "@web/views/fields/many2many_binary/many2many_binary_field";

const originalMethod = Many2ManyBinaryField.prototype.onFileRemove;
patch(MailComposerAttachmentList.prototype, {
    async onFileRemove(fileId) {
        if (originalMethod) {
            await originalMethod.call(this, fileId);
        }


        const attachment = this.mailStore.Attachment.insert(fileId);
        if (attachment) {
            await this.attachmentUploadService.unlink(attachment);
        }
        if (this.env.fullComposerBus) {
            this.env.fullComposerBus.trigger("ATTACHMENT_REMOVED", { id: attachment.id });
        }

    },
});