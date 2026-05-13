from odoo import models, fields
from odoo.exceptions import ValidationError
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification

class RemarkWizard(models.Model):
    _name = 'remark.wizard'
    _description = 'Remark Wizard'

    background_check_id = fields.Many2one('background.check.details', string="Background Check Details")
    remark = fields.Text(string="Remark", required=True)
    
    def action_submit(self):
        for rec in self:
            if rec.remark:
                if self.env.context.get('status') == 'submit':
                    rec.background_check_id.status = 'completed'
                if self.env.context.get('status') == 'cancel':
                    rec.background_check_id.status = 'cancelled'
                rec.background_check_id.remark = rec.remark


class RemarkWizard(models.TransientModel):
    _name = 'digital.evidence.confirm'
    _description = 'Digital Evidence Confirm'

    name = fields.Char()

    def action_redirect_to_case_investigation(self): 
        params = self.env.context.get('params',False)
        if params and params.get('project_id') and params.get('request_change_memo'):
            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Overarching Memo',
                    'res_model': 'overarching.memo',
                    'res_id': params.get('memo_id'),
                    'view_mode': 'form',
                    'target': 'main',
                }
        elif params and params.get('evidence_id') and params.get('is_de_request_change'):
            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Digital Evidence',
                    'res_model': 'digital.evidence',
                    'res_id': params.get('evidence_id'),
                    'view_mode': 'form',
                    'target': 'main',
                }
        elif params and params.get('project_id'):
            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Project',
                    'res_model': 'project.project',
                    'res_id': params.get('project_id'),
                    'view_mode': 'form',
                    'target': 'main',
                }
    

class RequestMemoChange(models.TransientModel):
    _name = 'request.memo.change'
    _description = 'Request Memo Change'

    name = fields.Text(required=True)

    def action_request_memo_change(self):
        memo_id = self.env['overarching.memo'].browse(self.env.context.get('active_id'))
        if memo_id.exists():
            memo_id.sudo().write({'memo_pending_at':'lead_investigator','request_change': self.name})

            model = memo_id._name
            for investigator in memo_id.lead_investigator_ids.ids:
                send_system_notification(
                    self.env,
                    message= f"Overarching Memo Request for changes – { memo_id.project_id.name }\n Action Required: Please review and resubmit the overarching memo.",
                    model= model,
                    user_id= investigator,
                    res_id= memo_id.id)
    
    def action_de_request_change(self):
        evidence_id = self.env['digital.evidence'].browse(self.env.context.get('active_id'))
        if evidence_id.exists():
            evidence_id.sudo().write({'digital_access':'lead_investigator','request_change': self.name})

            model = evidence_id._name
            for investigator in evidence_id.lead_investigator_ids.ids:
                send_system_notification(
                    self.env,
                    message= f"Digital Evidence Request for changes – { evidence_id.project_id.name }\n Action Required: Please review and resubmit the digital evidence.",
                    model= model,
                    user_id= investigator,
                    res_id= evidence_id.id)

class OutsourceReviewDocs(models.TransientModel):
    _name = 'outsource.review.docs'
    _description = 'Outsource Review Docs'

    attachment_ids = fields.Many2many('ir.attachment', string="Documents")

    def action_confirm(self):
        self.ensure_one()
        project_id = self.env.context.get('active_id')
        project = self.env['project.project'].browse(project_id)
        if project.exists():
            review_exist = self.env['forensic.peer.review'].search([('project_id','=',project.id)])
            if review_exist:
                review = review_exist
                review.sudo().write({'attachment_ids': [[6,0,self.attachment_ids.ids]]})
            else:
                review = self.env['forensic.peer.review'].create({
                    'project_id': project.id,
                    'state': 'in_progress',
                    'attachment_ids': [[6,0,self.attachment_ids.ids]],
                })
                project._move_project_stage()
            project.sudo().write({'is_external_report_submitted': True,
                                  'final_report_upload_date': fields.date.today()})
            if project.assigned_pfo_id:
                review_line_obj = self.env['forensic.peer.review.line'].create({
                    'review_id': review.id,
                    'user_id': project.user_id.id,
                    'action': 'pending',
                    'previous_reviewer_id': self.env.user.id
                    })
            else:
                raise ValidationError("Please assign Principle forensic officer.")
                    
            # System Notification
            model = review._name
            if model:
                res_model_id = self.env['ir.model'].search([('model','=',model)])
                if res_model_id and review_line_obj:
                    self.env['system.notification'].create({
                        'message':f"Report Awaiting Review – Investigation Report for {project.name} submitted.",
                        'user_id': review_line_obj.user_id.id,
                        "res_model_id":res_model_id.id or False,
                        "res_id":review.id
                    })
            return review