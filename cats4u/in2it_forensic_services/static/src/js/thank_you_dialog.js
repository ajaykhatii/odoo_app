import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { session } from "@web/session";
import { ThankYouDialog } from "@sign/dialogs/dialogs";
import { _t } from "@web/core/l10n/translation";


patch(ThankYouDialog.prototype, {
    async willStart() {
        const isEncrypted = await this.checkIfEncryptedDialog();
        if (isEncrypted) {
            this.dialog.add(EncryptedDialog);
        }

        this.signRequestState = await rpc(
            `/sign/sign_request_state/${this.signInfo.get("documentId")}/${this.signInfo.get(
                "signRequestToken"
            )}`
        );

        this.closeLabel = _t("Close");

        if (!session.is_frontend) {
            const closeResult = await this.orm.call("sign.request", "get_close_values", [
                [this.signInfo.get("documentId")],
            ]);
            this.closeAction = closeResult.action;
            this.closeLabel = closeResult.label;
            this.closeContext = closeResult.custom_action ? {} : { clearBreadcrumbs: true };
        }

        if (!this.suggestSignUp && !session.is_website_user) {
            const result = await rpc("/sign/sign_request_items", {
                request_id: this.signInfo.get("documentId"),
                token: this.signInfo.get("signRequestToken"),
            });

            if (result?.[0]?.case_ref_number) {
                this.message = `${result[0].case_ref_number} has been authorized`;
            } else if (result?.[0]?.evidence)  {
                this.message = `Request has been approved`;
            } 
            else if (result && result.length) {
                this.state.nextDocuments = result.map((doc) => ({
                    id: doc.id,
                    name: doc.name,
                    date: doc.date,
                    user: doc.user,
                    accessToken: doc.token,
                    requestId: doc.requestId,
                    canceled: false,
                }));
            }
           
        }

        this.generateButtons();
    },
});
