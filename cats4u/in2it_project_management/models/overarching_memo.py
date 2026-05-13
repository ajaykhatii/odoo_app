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
from odoo.exceptions import ValidationError
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification

class OverarchingMemo(models.Model):
    _name = "overarching.memo"
    _description = "Overarching Memo"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    name = fields.Char(string="Name", required=True, readonly=True, default=lambda self: _('New'), tracking=True)
    project_id = fields.Many2one('project.project', string="Project", tracking=True)
    case_id = fields.Many2one("crm.lead", string="Case", tracking=True)

    case_type = fields.Selection([('pre', 'PRE'),('for', 'FOR'),('lsa', 'LSA'),('dfo', 'DFO'),('eth', 'ETH')], string="Assignment Case Type", tracking=True)
    directorate_id = fields.Many2one("forensic.directorate", string="Directorate", tracking=True)
    allegation_nature_id = fields.Many2one("forensic.allegation.nature", string="Nature of Allegations", tracking=True)
    investigator_id = fields.Many2one("res.users", string="Investigation Manager", tracking=True)
    approval_date = fields.Date("Approval Date", tracking=True)
    status = fields.Selection([('pending','Pending'),('approved','Approved')], string="Status", tracking=True)
    sign_request_ids = fields.One2many('sign.request', 'overarching_memo_template_id', string="Signature Requests")
    remark = fields.Char("Remarks")
    memo_pending_at = fields.Selection([('lead_investigator','Pending at Lead Investigator'),('city_manager','awaiting CM authorization'),('ed','Feedback Awaited from ED'),('none','None')], string="Status", tracking=True)
    city_manager_id = fields.Many2one("res.users", string="City Manager")
    lead_investigator_ids = fields.Many2many("res.users", string="Investigator Name")
    request_change = fields.Text("Change", tracking=True)
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    document_line_ids = fields.One2many("forensic.document.line",compute="_compute_document_line_ids", string="Document Line")
    physical_item_ids = fields.One2many("complaint.physical.item",compute="_compute_document_line_ids", string="Document Line")
    assignment_type = fields.Selection(related="project_id.assignment_type", string="Case Handling Type", tracking=True)
    distribution_line_ids = fields.One2many("distribution.line", "memo_id", string="Document Line")

    @api.depends('project_id')
    def _compute_document_line_ids(self):
        for rec in self:
            rec.document_line_ids = rec.physical_item_ids = False
            if rec.project_id:
                if rec.project_id.document_line_ids:
                    doc_record = rec.project_id.document_line_ids.filtered(lambda r: r.is_annexure == True)
                    rec.document_line_ids = doc_record
                
                if rec.project_id.physical_item_ids:
                    doc_record = rec.project_id.physical_item_ids.filtered(lambda r: r.is_exhibit == True)
                    rec.physical_item_ids = doc_record

    @api.model_create_multi
    def create(self, vals_list):
        year = get_financial_year(self.env)
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                seq = self.env['ir.sequence'].next_by_code('overarching.memo.sequence') or '0000'
                vals['name'] = f"MEMO/{year}/{seq}"
        return super().create(vals_list)
    
    def action_approve_by_city_manager(self):
        for record in self:
            sign_request = record.sign_request_ids.sorted(
                key=lambda r: r.create_date or r.id,
                reverse=True
            )[:1]
            if sign_request:
                return sign_request.with_context({'sign_directly':True}).go_to_signable_document()

    def action_request_change_by_city_manager(self):
        return {
            'name': 'Request Change',
            'type': 'ir.actions.act_window',
            'res_model': 'request.memo.change',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'request_change_memo': True,
            }
        }
    
    def action_submit_by_lead_investigator(self):
        project_name = self.project_id.name if self.project_id else ""
        case_title = self.project_id.case_id.name if self.project_id and self.project_id.case_id else ""
        cm_subject = (
                f"{project_name}: ALLEGED { case_title.upper() }"
                if self.env.context.get('default_case_type') == 'pre'
                else f"{project_name} – FORENSIC INVESTIGATION INTO ALLEGED MISREPRESENTATION BY { case_title.upper() }"
            )
        subject = (
                f"{project_name}: ALLEGED { case_title.upper() }"
                if self.case_type == 'pre'
                else f"{ project_name } – FORENSIC INVESTIGATION INTO ALLEGED MISREPRESENTATION BY { case_title.upper() }"
            )
        return {
            'name': 'Overarching Memo',
            'type': 'ir.actions.act_window',
            'res_model': 'overarching.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'memo_id': self.id,
                'request_change_memo': True,
                'project_id': self.project_id.id,
                'users': self.city_manager_id.ids if self.city_manager_id else [],
                'default_subject': subject,
                'default_cm_subject': cm_subject,
                'approval_date': self.approval_date,
            }
        }
    
    def get_overarching_memo(self):
        user = self.env.user
        # Default: no records
        domain = [('id', '=', False)]
        if user.has_group('base.group_system') or user.has_group('in2it_forensic_services.group_fcm_admin'):
            domain = [] # show all records
        elif user.has_group('in2it_forensic_services.group_fcm_city_manager'):
            domain = [('city_manager_id', '=', user.id)]

        action = self.env.ref('in2it_project_management.overarching_memo_action')
        action.sudo().write({'domain': domain})
        return {
            'name': _('Overarching Memo'),
            'res_model': 'overarching.memo',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'id': action.id,
            'domain': domain,
            'context': {'search_default_pending': 1},
        }

    def action_preview_investigation_report(self):
        self.ensure_one()
        ed_users = self.project_id.distribution_line_ids.mapped('user_id').filtered(
            lambda u: u.position == 'ed'
        )
        if not ed_users:
            raise ValidationError("At least one ED must be in the distribution list.")
        return self.env.ref('in2it_project_management.action_investigation_report').report_action(self.project_id)
    
    def generate_preliminary_assessment_report(self):
        """Generate Preliminary assessment report"""
        self.ensure_one()
        return self.env.ref('in2it_project_management.action_pre_investigation_report').report_action(self.project_id.id)

    def write(self, vals):
        res = super().write(vals)

        for record in self:
            if vals.get('status') == 'approved':
                # Move Recommendation into Implementation
                chief = 'in2it_forensic_services.group_fcm_case_chief_access'
                recom_ids = record.project_id.recom_project_ids
                if recom_ids:
                    recom_ids.write({
                        'assign_by': self.env.user.id,
                        'assignment_date': fields.Date.today(),
                    })
                dl_ids = record.project_id.distribution_line_ids
                for_efs = dl_ids.filtered(lambda l: l.user_id and l.user_id.has_group(chief))
                for_not_efs = dl_ids

                efs_line = []
                not_efs_line = []
                for line in for_efs:
                    efs_line.append((0, 0, {
                        'user_id': line.user_id.id,
                        'action': line.action,
                        'for_efs': True,
                        'status': False if line.action == 'info' else 'pending'
                    }))

                for line in for_not_efs:
                    not_efs_line.append((0, 0, {
                        'user_id': line.user_id.id,
                        'action': line.action,
                        'status': False if line.action == 'info' else 'pending'
                    }))

                for rec in recom_ids:
                    if rec.for_efs:
                        rec.write({
                            'govt_action_line_ids': efs_line,
                        })
                    else:
                        rec.write({
                            'ed_action_line_ids': not_efs_line,
                        })

                # Sending system notification to Gov team and Chief
                chief_ids = dl_ids.filtered(
                    lambda l: l.user_id and l.action == 'action'
                              and l.user_id.has_group('in2it_forensic_services.group_fcm_case_chief_access')).mapped('user_id')

                governance_group = self.env.ref('in2it_project_management.group_cms_governance')
                governance_user_ids = self.env['res.users'].search([('groups_id', 'in', governance_group.id)])

                # Get first EFS recommendation safely
                efs_rec = recom_ids.filtered(lambda r: r.for_efs)[:1]
                if not efs_rec:
                    return

                message = (
                    f"You have been assigned a recommendation for implementation review. Action Required: Please review the recommendation.")

                model = efs_rec._name
                res_id = efs_rec.id

                # Combine users to avoid duplicate loops
                all_users = (chief_ids | governance_user_ids)

                for user in all_users:
                    send_system_notification(self.env, message, model, user.id, res_id)

                # Sending email to Executive Director
                dl_action_ed_ids = dl_ids.filtered(lambda l: l.user_id and l.action == 'action' and l.user_id.position == 'ed')
                dl_info_ed_ids = dl_ids.filtered(lambda l: l.user_id and l.action == 'info' and l.user_id.position == 'ed')
                template = False
                email_to = False

                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                url = f"{base_url}/my/home"

                if dl_action_ed_ids:
                    template = self.env.ref('in2it_project_management.mail_template_recommendation_assignment_ed_action')
                    email_to = ','.join(dl_action_ed_ids.mapped('user_id.partner_id.email'))
                    if template and email_to:
                        template.with_context({'url': url}).send_mail(
                            self.id,
                            email_values={'email_to': email_to},
                            force_send=True
                        )

                if dl_info_ed_ids:
                    template = self.env.ref('in2it_project_management.mail_template_recommendation_assignment_ed_info')
                    email_to = ','.join(dl_info_ed_ids.mapped('user_id.partner_id.email'))
                    if template and email_to:
                        template.with_context({'url': url}).send_mail(
                            self.id,
                            email_values={'email_to': email_to},
                            force_send=True
                        )

        return res
