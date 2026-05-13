# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class OverArchingMemoWizard(models.TransientModel):
    _name = "overarching.memo.wizard"
    _description = "Overarching Memo Wizard"

    project_id = fields.Many2one("project.project", string="Case Investigation")
    case_type = fields.Selection([('pre', 'PRE'),('for', 'FOR'),('lsa', 'LSA'),('dfo', 'DFO'),('eth', 'ETH')], default=False, string="Case Type")
    directorate_id = fields.Many2one("forensic.directorate", string="Directorate")
    allegation_nature_id = fields.Many2one("forensic.allegation.nature", string="Nature of Allegations")
    investigator_id = fields.Many2one("res.users", string="Investigation Manager")
    lead_investigator_ids = fields.Many2many("res.users", string="Investigators Name")
    approval_date = fields.Date("Approval Date")
    remark = fields.Char("Remarks")
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")

    def action_confirm(self):
        city_manager = self.env['res.users'].search([('groups_id','=',self.env.ref('in2it_forensic_services.group_fcm_city_manager').id)])
        project_id = self.env['project.project'].browse(self.env.context.get('active_id'))
        if project_id:
            case_title = project_id.case_id.name if project_id.case_id else ""
            cm_subject = (
                f"{project_id.name}: ALLEGED { case_title.upper() }"
                if self.env.context.get('default_case_type') == 'pre'
                else f"{project_id.name} – FORENSIC INVESTIGATION INTO ALLEGED MISREPRESENTATION BY { case_title.upper() }"
            )
            subject = (
                    f"{project_id.name}: ALLEGED { case_title.upper() }"
                    if self.case_type == 'pre'
                    else f"{ project_id.name } – FORENSIC INVESTIGATION INTO ALLEGED MISREPRESENTATION BY { case_title.upper() }"
                )
            return {
                'name': 'Overarching Memo',
                'type': 'ir.actions.act_window',
                'res_model': 'overarching.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'project_id': project_id.id,
                    'users': city_manager.ids if city_manager else [],
                    'default_subject': subject,
                    'default_cm_subject': cm_subject,
                    'remark': self.remark,
                    'attachments': self.attachment_ids.ids if self.attachment_ids else [],
                    'approval_date': self.approval_date or False
                }
            }
        else:
            raise ValidationError("Case Investigation not found.")