# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################


from odoo import models, fields, api, _
from datetime import datetime
import json
from base64 import b64encode
from odoo.exceptions import ValidationError, AccessError

class RequestAccessDigitalWizard(models.TransientModel):
    _name = "request.access.digital.wizard"
    _description = "Reuqest Access Digital Wizard"

    evidence_id = fields.Many2one('digital.evidence',string="Evidence")
    user_id = fields.Many2one("res.users", string="User")
    auth_body = fields.Html("Authorization Body")
    cm_user_id = fields.Many2one("res.users", string="User")
    cm_auth_body = fields.Html("Authorization Body")
    cm_subject = fields.Char(string="Subject")
    subject = fields.Char(string="Subject")
   
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project = self.env["project.project"].browse(self.env.context.get("project_id"))
        suspect = self.env['forensic.case.suspects'].browse(self.env.context.get('suspect_ids'))
        if project.exists():
            cm_template = self.env.ref('in2it_project_management.city_manager_approval_letter')
            cdo_template = self.env.ref('in2it_project_management.chief_digital_officer_approval_letter')
            ctx = {
                    "object": project, 
                    "suspect_ids": suspect if suspect else [],
                    "allegation_nature_id": project.allegation_nature_id.name,
                    "date_from": self.env.context.get('date_from'),
                    "date_to": self.env.context.get('date_to'),
                }
            if cm_template:
                rendered = self.env["ir.qweb"]._render(cm_template.id, ctx)
                res["cm_auth_body"] = rendered
     
            if cdo_template:
                rendered = self.env["ir.qweb"]._render(cdo_template.id, ctx)
                res["auth_body"] = rendered
        return res

    def action_confirm(self):
        project = self.env["project.project"].browse(self.env.context.get("project_id"))
        if project.exists():
            chief_id = project.chief_id
            signature_data = chief_id.sudo().sign_signature

            base_context = { 'name':self.env.user.name,
                        'job_position':self.env.user.employee_id.job_id.name,
                        'phone':self.env.user.employee_id.mobile_phone,
                        'mobile':self.env.user.work_phone,
                        'email':self.env.user.employee_id.work_email,
                        'allegation_nature': project.allegation_nature_id.name,
                        'department_name':self.env.user.employee_id.department_id.name,
                        'force_report_rendering': True,
                        'show_case_details': True,
                    }
            
            cm_context = dict(base_context, is_city_manager=True,
                                            city_manager= self.cm_user_id.name,
                                            sender_name= chief_id.name,
                                            sender_job_position= chief_id.employee_id.job_id.name,
                                            signature_bin= signature_data,
                                            subject= self.cm_subject,
                                            template_body= self.cm_auth_body)
            cdo_context = dict(base_context,is_cdo=True,
                                            cdo= self.user_id.name,
                                            sender_name= self.cm_user_id.name,
                                            sender_job_position= self.cm_user_id.employee_id.job_id.name,
                                            subject =self.subject,
                                            template_body= self.auth_body)
            
            report_obj = self.env['ir.actions.report']
            cm_pdf_content,_ = report_obj.with_context(**cm_context)._render_qweb_pdf('in2it_project_management.case_request_digital_access_cm_pdf_report', [project.id])
            cdo_pdf_content,_ = report_obj.with_context(**cdo_context)._render_qweb_pdf('in2it_project_management.case_request_digital_access_cm_pdf_report', [project.id])
            
            cm_generated_attachment = self.env['ir.attachment'].create({
                'name': f'request_digital_access_letter_{project.id}.pdf',
                'type': 'binary',
                'datas': b64encode(cm_pdf_content),
                'res_model': self.env.context.get('active_model') or False,
                'res_id': self.env.context.get('active_id') or False,
                'mimetype': 'application/pdf',
            })
            cdo_generated_attachment = self.env['ir.attachment'].create({
                    'name': f'request_digital_access_letter_{project.id}.pdf',
                    'type': 'binary',
                    'datas': b64encode(cdo_pdf_content),
                    'res_model': self.env.context.get('active_model') or False,
                    'res_id': self.env.context.get('active_id') or False,
                    'mimetype': 'application/pdf',
                })
            template = self.env['sign.template'].create({
                    'name': f'Evidence_letter_{self.id}.pdf',
                    'attachment_id': cdo_generated_attachment.id,
                    'user_id': self.user_id.id,
                    'subject':self.subject,
                    })
                
            template = template.with_context({'project_id': project.id,
                                              'city_manager': self.cm_user_id.id,
                                              'city_manager_partner_id': self.cm_user_id.partner_id.id,
                                              'suspect_ids': self.env.context.get('suspect_ids',False),
                                              'date_from':self.env.context.get('date_from',False),
                                              'date_to':self.env.context.get('date_to',False),
                                              'evidence':self.env.context.get('evidence',False),
                                              'comment':self.env.context.get('comment',False),
                                              'cm_letter': cm_generated_attachment.id or False,
                                              'is_de_request_change': self.env.context.get('is_de_request_change',False),
                                              'evidence_id': self.env.context.get('evidence_id',False)
                                              }).go_to_custom_template()

            return template

