# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
# from . import crm_lead_forensic
import logging

_logger = logging.getLogger(__name__)

def send_system_notification(env, message, model, user_id, res_id):
    if model:
        res_model_id = env['ir.model'].sudo().search([('model', '=', model)], limit=1)

        env['system.notification'].sudo().create({
            'message': message,
            'user_id': user_id,
            'res_model_id': res_model_id.id or False,
            'res_id': res_id,
        })

class ForensicCaseAssignment(models.Model):
    """Used to assign as specific case type"""
    _name = 'forensic.case.assignment'
    _description = 'Forensic Case Assignment'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "id desc"

    _rec_name = 'parent_case_id'

    parent_case_id = fields.Many2one('crm.lead', 'Internal Case Title', tracking=True, required=True)
    active = fields.Boolean(default=True,  tracking=True)
    parent_case_ref = fields.Char(related='parent_case_id.internal_coms_ref',
                                  string="Internal COMS Reference", readonly=True)
    case_ref_number = fields.Char(
        string='Case Reference No.',
        tracking=True,
        help="Auto-generated unique case reference number"
    )

    assignment_type_id = fields.Many2one(
        'forensic.assignment.type',
        string="Assignment Case Type",
        required=True,
        tracking=True
    )
    is_authorise = fields.Boolean(related="assignment_type_id.is_authorize")
    is_unauthorized = fields.Boolean(string="Is Unauthorized")
    stage_id = fields.Many2one(
        'forensic.assignment.stage',
        string="Stage",
        tracking=True,
    )
    associated_stage_ids = fields.Many2many('forensic.assignment.stage', string="Associated Stage",
                                            help = "Helper field - automatically filled based on assignment type")
    
    allegation_nature_id = fields.Many2one('forensic.allegation.nature', string="Nature of Allegations", related="parent_case_id.allegation_nature_id")
    reporting_date = fields.Datetime("Reporting Date",related="parent_case_id.create_date")
    partner_id = fields.Many2one(
        string='Complainant',
        comodel_name='res.partner',
        related="parent_case_id.partner_id"
    )
    department_id = fields.Many2one(
        'forensic.department',
        string='Department',
        related="parent_case_id.department_id"
    )
    directorate_id = fields.Many2one(
        'forensic.directorate',
        string='Directorate',
        related="parent_case_id.directorate_id"
    )
    auth_html_content = fields.Html(string="Authorization HTML Content")
    auth_signature = fields.Binary()
    auth_subject = fields.Char(string="Subject")

    forensic_member_ids = fields.One2many(
        comodel_name='forensic.investigation.team',
        inverse_name='case_assignment_id',
        string="Members",
        help='List of investigation members linked to this case.'
    )

    lead_investigator_ids = fields.Many2many(
        'res.users',
        string='Lead Investigator',
        help='Lead Investigator must be selected from investigation team members only.'
    )

    available_team_lead_ids = fields.Many2many(
        'res.users',
        compute='_compute_available_team_leads',
        store=False
    )
    button_visibility = fields.Selection([('under_auth', 'Under Auth'), ('sign_auth', 'Sign & Auth'), ('download', 'Download')],
                                         default='under_auth', string='Button Visibility')

    case_age = fields.Char("Case Aging",compute="_compute_case_age")

    investigation_manager_id = fields.Many2one('hr.employee', string='Investigation Manager',
                                               domain=lambda self: [('id', 'in', self.env['hr.department'].search([
                                                   ('manager_id', '!=', False)
                                               ]).mapped('manager_id').ids)])
    reason = fields.Char("Reason", help="This is Unauthorized reason")
    is_inv_last_stage = fields.Boolean(string='Is Investigation Last Stage', compute='_get_investigation_last_stage')
    physical_item_ids = fields.One2many(
        comodel_name='complaint.physical.item',
        inverse_name='case_assignment_id',
        string="Physical Items Received"
    )
    document_line_ids = fields.One2many(comodel_name='forensic.document.line', inverse_name="case_assignment_id", string="Document Line")
    assignment_is_lin = fields.Boolean(
        compute="_compute_assignment_is_lin",
        store=True
    )
    file_data = fields.Binary("Report File")
    file_name = fields.Char("File Name")
    report_submitted_by = fields.Many2one("res.partner",string="Report Submitted By")
    report_history_ids = fields.One2many(
        'ir.attachment',
        'assignment_id',
        string="Report History"
    )

    @api.depends('assignment_type_id')
    def _compute_assignment_is_lin(self):
        LIN = self.env.ref('in2it_forensic_services.assignment_type_line_refferal')
        for rec in self:
            rec.assignment_is_lin = rec.assignment_type_id == LIN


    def _get_investigation_last_stage(self):
        self.is_inv_last_stage = False
        for rec in self:
            project = self.env['project.project'].search([('assignment_id', '=', rec.id)])
            if project and project.stage_id == self.env.ref('project.project_project_stage_3'):
                rec.is_inv_last_stage = True


    def _compute_case_age(self):
        underauthorised_stage = self.env.ref('in2it_forensic_services.case_type_stage_under_authorisation',raise_if_not_found=False)
        stage_id = underauthorised_stage.id if underauthorised_stage else 0
        for record in self:
            if record.stage_id.id != stage_id:
                days = (fields.Datetime.now() - record.create_date).days

                record.case_age = days
            else:
                record.case_age = 0
            


    @api.depends('forensic_member_ids.member_ids')
    def _compute_available_team_leads(self):
        for record in self:
            record.available_team_lead_ids = (
                record.forensic_member_ids
                .mapped('member_ids')
            )



    def _compute_associated_stage(self):
        for rec in self:
            if rec.assignment_type_id:
                stages = rec.assignment_type_id.stage_ids.sorted(lambda s: (s.sequence, s.id))
                rec.associated_stage_ids = stages.ids
            else:
                rec.associated_stage_ids = False


    def send_authorisation_details_with_attachment(self):
        self.ensure_one()
        authority_id = self.assignment_type_id.authority_id if self.assignment_type_id.authority_id else False
        job_chief_id = self.env.ref('in2it_forensic_services.chief').id
        if authority_id.id == job_chief_id:
            users = self.env['res.users'].search([('groups_id','=',self.env.ref('in2it_forensic_services.group_fcm_case_chief_access').id)])
        else:
            users = self.env['res.users'].search([('groups_id','=',self.env.ref('in2it_forensic_services.group_fcm_city_manager').id)])

        return {
            'name': 'Case Authorization',
            'type': 'ir.actions.act_window',
            'res_model': 'casetype.authorize.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'users': users.ids if users else []
            }
        }
    
    def _compute_access_url(self):
        super()._compute_access_url()
        for case in self:
            case.access_url = f'/my/cases/{case.id}'

    # Esign
    sign_request_ids = fields.One2many('sign.request', 'authorization_template_id', string="Signature Requests")

    def sign_authorize(self):
        for record in self:
            sign_request = record.sign_request_ids.sorted(
                key=lambda r: r.create_date or r.id,
                reverse=True
            )[:1]
            if sign_request:
                return sign_request.with_context({'sign_directly':True}).go_to_signable_document()

    def get_completed_document(self):
        for record in self:
            get_document = record.sign_request_ids.sorted(
                key=lambda r: r.create_date or r.id,
                reverse=True
            )[:1]

            if get_document:
                return get_document.get_completed_document()
            
    assignment_type_ids = fields.Many2many('forensic.assignment.type', string="Changes Type", tracking=True)
    comment = fields.Text(string="Comment", tracking=True)
    

    record_link = fields.Html(
        string="New Request",
        readonly=True,
        sanitize=False,
    )

    is_new_request = fields.Boolean(default=False)

    def action_change_request(self):
        for rec in self:
            if not rec.stage_id:
                raise ValidationError("Please configure stage for the case assignment.")
        return {
        'name': 'Change Request',
        'type': 'ir.actions.act_window',
        'res_model': 'change.request.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'case_auth_id': self.id,
            'assignment_type_id':self.assignment_type_id.id,
        }
    }


    def preview_schedule_of_complaints(self):
        self.ensure_one()

        return {
            'name': 'Schedule of Complaints',
            'type': 'ir.actions.act_window',
            'res_model': 'schedule.of.complaints.display',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_parent_case_id': self.parent_case_id.id,
                'default_case_ref_number': self.case_ref_number,
                'default_create_date': self.parent_case_id.create_date,
                'default_assignment_type_id': self.assignment_type_id.id,
            }
        }

    def related_stakeholder_team(self):
        emails = set()

        dept_sfo_id = self.env.ref("in2it_forensic_services.group_fcm_case_sfo_access", raise_if_not_found=False).id
        dept_fo_id = self.env.ref("in2it_forensic_services.group_fcm_case_fo_access", raise_if_not_found=False).id
        emails = self.env['res.users'].search([('groups_id', 'in', [dept_sfo_id,dept_fo_id])]).mapped('employee_id.work_email')

        email_to = ', '.join(sorted(emails))
        return email_to

    def action_case_unauthorize(self):
        self.ensure_one()
        return {
            'name': 'Case Unauthorized',
            'type': 'ir.actions.act_window',
            'res_model': 'case.unauthorized.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_case_assignment_id': self.id,
            }
        }

    def get_relevent_users(self):
        """This function is used to get email of SFO,PFO and FO from the governance team."""
        stakeholder_email = set()

        sfo_id = self.env.ref("in2it_forensic_services.senior_forensic_officer", raise_if_not_found=False).id
        fo_id = self.env.ref("in2it_forensic_services.forensic_officer", raise_if_not_found=False).id
        pfo_id = self.env.ref("in2it_forensic_services.principle_of_forensic_officer", raise_if_not_found=False).id

        stakeholder_email = self.env['hr.employee'].search([('job_id','in',[sfo_id,fo_id,pfo_id])]).mapped('work_email')
        email_to = ', '.join(sorted(stakeholder_email))
        return email_to

    def filtered_case_authorization(self):
        user = self.env.user
        list_view = self.env.ref('in2it_forensic_services.view_forensic_case_assignment_city_manager_list').id
        form_view = self.env.ref('in2it_forensic_services.view_forensic_case_assignment_form').id
        if user.has_group('base.group_system') or user.has_group('in2it_forensic_services.group_fcm_admin'):
            domain = [(1, '=', 1)]
        else:
            domain = [('assignment_type_id.authority_id', '=', user.employee_id.job_id.id)]

        action = self.env.ref('in2it_forensic_services.action_forensic_case_authorization')
        action.sudo().write({'domain': domain})
        return {
            'name': _('Case Authorization'),
            'res_model': 'forensic.case.assignment',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'views': [(list_view, 'list'), (form_view, 'form')],
            'view_id': list_view,
            'id': action.id,
            'context': {
                'create': False,
                'search_default_pending_stage': 1,
                'sign_auth': True
            },
            'domain': domain,
            'help': """
                        <p class="o_view_nocontent_smiling_face">Case Authorization.</p>
                        <p>Odoo helps you track all case authorization.</p>
                    """
        }

class SignRequest(models.Model):
    _inherit = "sign.request"

    authorization_template_id = fields.Many2one('forensic.case.assignment', string="Authorization Template")


class InheritIrAttachment(models.Model):
    _inherit = "ir.attachment"

    assignment_id = fields.Many2one(
        'forensic.case.assignment',
        string="Case Assignment"
    )

