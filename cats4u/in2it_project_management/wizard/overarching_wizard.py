# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################


from odoo import models, fields, api, _
import json
from base64 import b64encode


class OverarchingWizard(models.TransientModel):
    _name = "overarching.wizard"
    _description = "Overarching Wizard"
   
    user_id = fields.Many2one("res.users", string="User")
    subject = fields.Char(string="Subject")
    auth_body = fields.Html("Authorization Body")
    cm_auth_body = fields.Html("Authorization Body")
    cm_subject = fields.Char(string="Subject")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project = self.env["project.project"].browse(self.env.context.get("project_id"))
        if project.exists():
            if project.case_type == 'pre':
                cm_template = self.env.ref('in2it_project_management.city_manager_overarching_pre_memo_letter')
                ed_template = self.env.ref('in2it_project_management.executive_officer_overarching_pre_memo_letter')
            else:
                cm_template = self.env.ref('in2it_project_management.city_manager_overarching_for_lsa_dfo_eth_memo_letter')
                ed_template = self.env.ref('in2it_project_management.executive_officer_overarching_for_lsa_dfo_eth_memo_letter')
            ctx = {
                    "object": project,
                    "approval_date": self.env.context.get('approval_date')
                }
            if cm_template:
                rendered = self.env["ir.qweb"]._render(cm_template.id, ctx)
                res["cm_auth_body"] = rendered
            if ed_template:
                rendered = self.env["ir.qweb"]._render(ed_template.id, ctx)
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
                    'department_name':self.env.user.employee_id.department_id.name,
                    'force_report_rendering': True,
                    'show_case_details': True,
                }
            cm_context = dict(base_context, is_city_manager=True,
                                            city_manager= self.user_id.name,
                                            sender_name= chief_id.name,
                                            sender_job_position= chief_id.employee_id.job_id.name,
                                            signature_bin= signature_data,
                                            subject= self.cm_subject,
                                            template_body= self.cm_auth_body)
            ed_context = dict(base_context,is_ed=True,
                                            sender_name= self.user_id.name,
                                            sender_job_position= self.user_id.employee_id.job_id.name,
                                            subject =self.subject,
                                            template_body= self.auth_body)
            
            report_obj = self.env['ir.actions.report']
            cm_pdf_content,_ = report_obj.with_context(**cm_context)._render_qweb_pdf('in2it_project_management.overarching_pre_memo_city_manager_pdf_report', [project.id])
            ed_pdf_content,_ = report_obj.with_context(**ed_context)._render_qweb_pdf('in2it_project_management.overarching_pre_memo_ed_pdf_report', [project.id])

            cm_generated_attachment = self.env['ir.attachment'].create({
                'name': f'Overarching_memo_CM_letter_{project.name}.pdf',
                'type': 'binary',
                'datas': b64encode(cm_pdf_content),
                'res_model': self.env.context.get('active_model') or False,
                'res_id': self.env.context.get('active_id') or False,
                'mimetype': 'application/pdf',
            })
            ed_generated_attachment = self.env['ir.attachment'].create({
                'name': f'Overarching_memo_letter_{project.name}.pdf',
                'type': 'binary',
                'datas': b64encode(ed_pdf_content),
                'res_model': self.env.context.get('active_model') or False,
                'res_id': self.env.context.get('active_id') or False,
                'mimetype': 'application/pdf',
            })

            template = self.env['sign.template'].create({
                'name': f'Overarching_memo_letter_{project.name}.pdf',
                'attachment_id': ed_generated_attachment.id,
                'user_id': self.user_id.id,
                'subject':self.subject,
                })
            
            template = template.with_context({'cm_letter': cm_generated_attachment.id or False,
                                              'city_manager_partner_id': self.user_id.partner_id.id,
                                              'city_manager_memo': self.user_id.id,
                                              'project_id': project.id,
                                              'case_id': project.case_id.id,
                                              'case_type': project.case_type,
                                              'directorate_id': project.directorate_id.id,
                                              'allegation_nature_id': project.allegation_nature_id.id,
                                              'investigator_id': project.user_id.id,
                                              'lead_investigator_ids': (project.assigned_forensic_team_id.project_investigator_ids.ids
                                                                        if project.assignment_type == 'internal'
                                                                        else [project.assigned_pfo_id.id] if project.assigned_pfo_id else []),
                                               'approval_date': self.env.context.get('approval_date'),
                                               'attachments': self.env.context.get('attachments'),
                                               'remark': self.env.context.get('remark'),
                                               'request_change_memo': self.env.context.get('request_change_memo'),
                                               'memo_id': self.env.context.get('memo_id',False)
                                              }).go_to_custom_template()
            return template
        