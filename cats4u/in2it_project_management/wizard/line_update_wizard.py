from odoo import models, fields

class CommentWizard(models.TransientModel):
    _name = 'comment.wizard'
    _description = 'Comment Wizard'

    comment = fields.Text(string="Comment", required=True)

    def action_submit_comment(self):
        model = self.env.context.get('active_model')
        res_id = self.env.context.get('active_id')

        record = self.env[model].browse(res_id)

        if record.exists() and record.report_submitted_by:
            partner = record.report_submitted_by
            record.message_subscribe(partner_ids=[partner.id])

            record.message_post(
                body=self.comment,
                subtype_xmlid='mail.mt_comment',
                message_type='comment'
            )
            record.report_submitted_by = False

