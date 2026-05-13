from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import os
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification


class RecommendationSubmitFeedback(models.TransientModel):
    _name = 'recom.submit.feedback.wizard'
    _description = 'Recommendation Submit Feedback Wizard'

    recom_action_id = fields.Many2one("ed.action.line", string="Project Category")
    remark = fields.Text(string="Remarks")
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Attachment"
    )
    status = fields.Selection([
        ('disputed', 'Disputed'),
        ('completed', 'Completed')], string="Status", default="disputed")

    def action_Submit(self):
        for rec in self:
            if rec.recom_action_id and rec.remark and rec.attachment_ids and rec.status:
                action = rec.recom_action_id

                # Update fields
                action.write({
                    'remark': rec.remark,
                    'attachment_ids': rec.attachment_ids,
                    'status': rec.status,
                    'action_date': fields.Datetime.now(),
                    'action_by': self.env.user.id,
                })
                recom_id = action.gov_recom_id or action.recom_id
                project = recom_id.project_id

                # Collect users
                users = (
                        project.user_id
                        | project.chief_id
                        | project.assigned_forensic_team_id.project_investigator_ids
                )

                # Exclude current user and remove empty users
                users = users.filtered(lambda u: u and u.id != self.env.user.id)

                message = (
                    "A recommendation assigned for governance review has been reviewed and recorded with attachment."
                )

                model = 'ed.action.line'
                res_id = action.id

                # Send notifications
                for user in users:
                    send_system_notification(self.env, message, model, user.id, res_id)

    @api.constrains('attachment_ids')
    def _check_attachment_type(self):
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
        for rec in self:
            for attachment in rec.attachment_ids:
                _, ext = os.path.splitext(attachment.name or '')
                if ext.lower() not in allowed_extensions:
                    raise ValidationError(
                        f"Invalid attachment type: {attachment.name}"
                    )

