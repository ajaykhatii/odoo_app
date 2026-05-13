/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SignablePDFIframe } from "@sign/components/sign_request/signable_PDF_iframe";
import { formatDateTime } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";

const { DateTime } = luxon;
patch(SignablePDFIframe.prototype, {
    enableCustom(signItem) {
        super.enableCustom(signItem);

        if (this.readonly || signItem.data.responsible !== this.currentRole) {
            return;
        }
        const signItemElement = signItem.el;
        console.log("signeitem",signItem)
        const signItemType = this.signItemTypesById[signItem.data.type_id];

        if (signItemType.name === _t("Date & Time")) {
            signItemElement.addEventListener("focus", (e) => {
                if (!e.currentTarget.value) {
                    this.fillTextSignItem(
                        e.currentTarget,
                        formatDateTime(DateTime.fromJSDate(new Date()))
                    );
                }
            });
        }
    },
});

