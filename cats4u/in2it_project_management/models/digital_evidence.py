# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from datetime import datetime
from ...in2it_forensic_services.models.crm_lead_forensic import get_financial_year

class DigitalEvidence(models.Model):
    _name = "digital.evidence"
    _description = "Digital Evidence"
    _rec_name = "name"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    name = fields.Char("Name", required=True, readonly=True, default=lambda self: _('New'), tracking=True)
    project_id = fields.Many2one("project.project", string="Case Investigation", required=True, tracking=True)
    date_from = fields.Date("Date Start", tracking=True)
    date_to = fields.Date("Date To", tracking=True)
    digital_access = fields.Selection([('lead_investigator','Pending at Lead Investigator'),('city_manager','Pending at City Manager'),('cdo','Pending at Chief Digital Officer')], string="Digital Access", tracking=True)
    comment = fields.Text("Comment", tracking=True)
    status = fields.Selection([('pending','Pending'),('approved','Approved')], string="Status", tracking=True)
    suspect_ids = fields.Many2many('forensic.case.suspects', string="Suspects", tracking=True)
    auth_html_content = fields.Html(string="Authorization HTML Content")
    auth_signature = fields.Binary()
    auth_subject = fields.Char(string="Subject")
    sign_request_ids = fields.One2many('sign.request', 'evidence_template_id', string="Signature Requests")
    lead_investigator_ids = fields.Many2many("res.users", related="project_id.assigned_forensic_team_id.project_investigator_ids")
    city_manager_id = fields.Many2one("res.users",string="City Manager")
    evidence = fields.Text("Evidence", tracking=True)
    attachment_ids = fields.Many2many("ir.attachment", string="Letters")
    request_change = fields.Text("Change", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        year = get_financial_year(self.env)
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                seq = self.env['ir.sequence'].next_by_code('digital.evidence.sequence') or '0000'
                vals['name'] = f"DE/{year}/{seq}"
        return super().create(vals_list)

    def action_request_change_by_city_manager(self):
        return {
            'name': 'Request Change',
            'type': 'ir.actions.act_window',
            'res_model': 'request.memo.change',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'is_de_request_change_cm': True,
            }
        }

    def action_submit_de_lead_investigator(self):
        self.ensure_one()
        chief_digital_officer = self.env['res.users'].search([('position', '=', 'cdo')])
        return {
            'name': 'Request for Digital Access',
            'type': 'ir.actions.act_window',
            'res_model': 'request.access.digital.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'is_de_request_change': True,
                'project_id': self.project_id.id,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'comment': self.comment,
                'suspect_ids': self.suspect_ids.ids,
                'cm_users': [self.city_manager_id.id] if self.city_manager_id else [],
                'cdo_users': chief_digital_officer.ids if chief_digital_officer else [],
                'evidence_id': self.id,
                'default_cm_subject': "REQUEST FOR THE AUTHORISATION OF EMAIL COLLECTION AND SEARCH CRITERIA TO BE USED IN RESPECT OF FS304/24-25: ALLEGED UIFW EXPENDITURE AND MISMANAGEMENT OF FUNDS",
                'default_subject': "REQUEST FOR THE AUTHORISATION OF EMAIL COLLECTION AND SEARCH CRITERIA TO BE USED IN RESPECT OF XXXX",
            }
        }

    def action_sign_by_city_manager(self):
        for record in self:
            sign_request = record.sign_request_ids.sorted(
                key=lambda r: r.create_date or r.id,
                reverse=True
            )[:1]
            if sign_request:
                return sign_request.with_context({'sign_directly':True}).go_to_signable_document()

    def get_digital_evidence(self):
        user = self.env.user
        # Default: no records
        domain = [('id', '=', False)]
        if user.has_group('base.group_system') or user.has_group('in2it_forensic_services.group_fcm_admin'):
            domain = [] # show all records
        elif user.has_group('in2it_forensic_services.group_fcm_city_manager'):
            domain = [('city_manager_id', '=', user.id)]

        action = self.env.ref('in2it_project_management.digital_evidence_action')
        action.sudo().write({'domain': domain})
        return {
            'name': _('Digital Evidence'),
            'res_model': 'digital.evidence',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'id': action.id,
            'domain': domain,
            'context': {'search_default_pending': 1}
        }

class SignRequest(models.Model):
    _inherit = "sign.request"

    evidence_template_id = fields.Many2one('digital.evidence', string="Evidence Template")
    overarching_memo_template_id = fields.Many2one('overarching.memo', string="Overarching Memo Template")