# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields
from odoo.exceptions import UserError
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification

class SignTemplate(models.Model):
    _inherit = "sign.template"

    evidence_id = fields.Many2one('digital.evidence', string="Authorization Template")
    user_id = fields.Many2one("res.users", string="User")
    subject = fields.Char(string="Subject")

    def send_custom_email(self,attachment_id,params):
        self.ensure_one()
        if params:
            if params.get('project_id') and params.get('city_manager'):
                cm_role = self.env.ref('in2it_project_management.sign_item_role_city_manager').id
                cdo_role = self.env.ref('in2it_project_management.sign_item_role_chief_digital_officer').id

                template_roles = self.sign_item_ids.mapped('responsible_id').ids
                if cm_role not in template_roles and cdo_role not in template_roles:
                    raise UserError("Please select city manager and CDO role.")
                
                elif cm_role not in template_roles:
                    raise UserError("Please select City Manager role.")
                
                elif cdo_role not in template_roles:
                    raise UserError("Please select Chief Digital Officer role.")
                
                if set(template_roles) != {cm_role,cdo_role}:
                    raise UserError("Please select appropriate role.")

                if params.get('is_de_request_change'):
                    evidence_id = self.env['digital.evidence'].search([('id','=',params.get('evidence_id'))])
                else:
                    vals = {
                    'project_id': params.get('project_id') or False,
                    'date_from': params.get('date_from') or False,
                    'date_to': params.get('date_to') or False,
                    'comment': params.get('comment') or '',
                    'status': 'pending',
                    'digital_access': 'city_manager',
                    'suspect_ids': [[6,0,params.get('suspect_ids')]],
                    'evidence': params.get('evidence') or False,
                    'city_manager_id': params.get('city_manager') or False,
                    'attachment_ids': [(6, 0, [params.get('cm_letter')])]
                    }
                    evidence_id = self.env['digital.evidence'].sudo().create(vals)
                email_values = {
                        'attachment_ids': [(6, 0, [attachment_id,params.get('cm_letter')])],
                        'email_to': self.user_id.employee_id.work_email,
                    }
                
                template = self.env.ref("in2it_project_management.mail_template_case_request_digital_access_city_manager")
                if template:
                    template.with_context({'subject': self.subject}).send_mail(evidence_id.id, email_values=email_values,force_send=True)
                    sign_request = self.env['sign.request'].with_context(skip_sign_access_mail=True
                        ).create({
                            'evidence_template_id': evidence_id.id,
                            'template_id': self.id,
                            'reference': f'Evidence_letter_{self.id}.pdf',
                            'request_item_ids': [(0, 0, {
                                    'partner_id': params.get('city_manager_partner_id'),
                                    'role_id': self.env.ref('in2it_project_management.sign_item_role_city_manager').id,
                                    'mail_sent_order': 1,
                                }),(0, 0, {
                                    'partner_id': self.user_id.partner_id.id,
                                    'role_id': self.env.ref('in2it_project_management.sign_item_role_chief_digital_officer').id,
                                    'mail_sent_order': 2,
                            })],
                        })
                if params.get('is_de_request_change'):
                    evidence_id.sudo().write({'digital_access':'city_manager'})
                model = evidence_id._name
                if model:
                    res_model_id = self.env['ir.model'].search([('model','=',model)])
                if res_model_id:
                    #system notification to City manager
                    self.env['system.notification'].create({
                        'message':f"A Digital Access Permission Request for Case: { evidence_id.project_id.name } has been submitted for your approval.\nPlease review the permission letter.",
                        'user_id': params.get('city_manager'),
                        "res_model_id": res_model_id.id or False,
                        "res_id": evidence_id.id,
                    })
                    # system notification for Chief
                    self.env['system.notification'].create({
                        'message':f"A new Digital Access Request has been submitted by { self.env.user.name } for Case: { evidence_id.project_id.name }.\nPlease review the request.",
                        'user_id': evidence_id.project_id.chief_id.id,
                        "res_model_id": res_model_id.id or False,
                        "res_id": evidence_id.id,
                    })
            elif params.get('project_id') and params.get('city_manager_memo'):
                cm_role = self.env.ref('in2it_project_management.sign_item_role_city_manager').id
                template_roles = self.sign_item_ids.mapped('responsible_id').ids
                if cm_role not in template_roles:
                    raise UserError("Please select City Manager role.")
                
                if set(template_roles) != {cm_role}:
                    raise UserError("Please select appropriate role.")
                
                if params.get('request_change_memo'):
                    memo_id = self.env['overarching.memo'].search([('id','=',params.get('memo_id'))])
                else:
                    vals = {
                        'project_id': params.get('project_id') or False,
                        'case_id': params.get('case_id') or False,
                        'case_type': params.get('case_type',False),
                        'directorate_id': params.get('directorate_id') or False,
                        'allegation_nature_id': params.get('allegation_nature_id') or False,
                        'investigator_id': params.get('investigator_id') or False,
                        'lead_investigator_ids': params.get('lead_investigator_ids') or False,
                        'approval_date': params.get('approval_date') or False,
                        'remark': params.get('remark') or False,
                        'status': 'pending',
                        'city_manager_id': params.get('city_manager_memo',False),
                        'memo_pending_at': 'city_manager',
                        'attachment_ids':[(6, 0, params.get('attachments'))]
                    }
                    memo_id = self.env['overarching.memo'].sudo().create(vals)
                    
                    recommendation = memo_id.project_id.recom_project_ids.filtered(lambda l: not l.for_efs)
                    if recommendation:
                        distribution_line = memo_id.project_id.distribution_line_ids.filtered(lambda line: line.action == 'action' and line.user_id and line.user_id.position == 'ed')
                        for line in distribution_line:
                            vals = {
                                'action': line.action,
                                'user_id': line.user_id.id,
                                'status': 'pending',
                                'memo_id': memo_id.id,
                                'active': True,
                            }
                            new_line = self.env['distribution.line'].sudo().create(vals)
                sign_request = self.env['sign.request'].with_context(skip_sign_access_mail=True
                ).create({
                    'overarching_memo_template_id': memo_id.id,
                    'template_id': self.id,
                    'reference': f"Overarching_memo_{memo_id.id}.pdf",
                    'request_item_ids': [(0, 0, {
                                'partner_id': params.get('city_manager_partner_id'),
                                'role_id': self.env.ref('in2it_project_management.sign_item_role_city_manager').id,
                            })]
                    })
                if params.get('request_change_memo'):
                    memo_id.sudo().write({'memo_pending_at':'city_manager'})
                
                email_values={
                    'attachment_ids': [(6, 0, [attachment_id,params.get('cm_letter')])],
                    'email_to': self.user_id.employee_id.work_email,
                }
                template = self.env.ref("in2it_project_management.mail_template_case_overarching_memo_city_manager")
                if template:
                    template.send_mail(memo_id.id, email_values=email_values, force_send=True)
                
                user_id = memo_id.city_manager_id.id,
                res_id = memo_id.id
                model = memo_id._name
                message = f"Overarching Memo Submitted for Authorization – { memo_id.project_id.name } Action Required: Please review and authorize the overarching memo."
                if user_id and res_id and model:
                    send_system_notification(self.env,message,model,user_id,res_id)   #system notification to City manager
        return {'type': 'ir.actions.act_window_close'}
    

    def go_to_custom_template(self, sign_directly_without_mail=False):
        self.ensure_one()
        return {
            'name': "Template \"%(name)s\"" % {'name': self.attachment_id.name},
            'type': 'ir.actions.client',
            'tag': 'sign.Template',
            'params': {
                'id': self.id,
                'sign_directly_without_mail': sign_directly_without_mail,
                'project_id': self.env.context.get('project_id',False),
                'city_manager': self.env.context.get('city_manager',False),
                'city_manager_partner_id': self.env.context.get('city_manager_partner_id',False),
                'suspect_ids': self.env.context.get('suspect_ids',False),
                'date_from':self.env.context.get('date_from',False),
                'date_to':self.env.context.get('date_to',False),
                'evidence':self.env.context.get('evidence',False),
                'comment':self.env.context.get('comment',False),
                'cm_letter': self.env.context.get('cm_letter',False),
                'is_de_request_change': self.env.context.get('is_de_request_change',False),
                'evidence_id': self.env.context.get('evidence_id',False),
                'city_manager_memo': self.env.context.get('city_manager_memo',False),
                'request_change_memo': self.env.context.get('request_change_memo',False),
                
                'case_id': self.env.context.get('case_id',False),
                'memo_id': self.env.context.get('memo_id',False),
                'case_type': self.env.context.get('case_type',False),
                'directorate_id': self.env.context.get('directorate_id',False),
                'allegation_nature_id': self.env.context.get('allegation_nature_id',False),
                'investigator_id': self.env.context.get('investigator_id',False),
                'lead_investigator_ids': self.env.context.get('lead_investigator_ids',False),
                'approval_date': self.env.context.get('approval_date',False),
                'remark': self.env.context.get('remark',False),
                'attachments': self.env.context.get('attachments',False),
            },
        }