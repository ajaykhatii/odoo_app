# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from . import crm_lead_forensic
import logging

_logger = logging.getLogger(__name__)

class ForensicInvestigationTeam(models.Model):
    """Used to assign member to a particular team"""
    _name = 'forensic.investigation.team'
    _description = 'Forensic Investigation Team'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    case_assignment_id = fields.Many2one('forensic.case.assignment', string='Case Assignment', ondelete='cascade')
    unit_id = fields.Many2one('hr.department', 'Unit', tracking=True)
    active = fields.Boolean(default=True,  tracking=True)
    sequence = fields.Integer(default=10, tracking=True)
    job_id = fields.Many2one('hr.job', string='Job Position', tracking=True)
    member_ids = fields.Many2many('res.users', string='Members', tracking=True)

    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        self.job_id = False
        self.member_ids = False

    @api.onchange('job_id')
    def _onchange_job_id(self):
        self.member_ids = False

    @api.constrains('case_assignment_id', 'unit_id', 'job_id')
    def _check_unique_unit_job_per_case(self):
        for record in self:
            if not record.case_assignment_id or not record.unit_id or not record.job_id:
                continue

            domain = [
                ('case_assignment_id', '=', record.case_assignment_id.id),
                ('unit_id', '=', record.unit_id.id),
                ('job_id', '=', record.job_id.id),
                ('id', '!=', record.id),
            ]

            if self.search_count(domain):
                raise ValidationError(_(
                    "The Job Position '%s' is already assigned to Unit '%s' "
                    "for this Investigation Team. Duplicate entries are not allowed."
                ) % (record.job_id.display_name, record.unit_id.display_name))



class HrJobForensic(models.Model):
    _inherit = 'hr.job'

    unit_ids = fields.Many2many('hr.department', 'Units', tracking=True)
    job_desc = fields.Text('Description')

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    job_count = fields.Integer(
        string='Jobs',
        compute='_compute_job_count'
    )
    is_forensic_dep = fields.Boolean(string='Is Forensic Department', tracking=True, help='Flag to identify Department related to Forensic')

    def _compute_job_count(self):
        job_obj = self.env['hr.job']
        for department in self:
            department.job_count = job_obj.search_count([
                ('unit_ids', 'in', department.id)
            ])

    def action_view_jobs(self):
        self.ensure_one()
        return {
            'name': 'Jobs',
            'type': 'ir.actions.act_window',
            'res_model': 'hr.job',
            'view_mode': 'list,form',
            'domain': [('unit_ids', 'in', self.id)],
            'context': {
                'default_unit_ids': self.id
            }
        }

class HrEmployeeForensic(models.Model):
    _inherit = 'hr.employee'

    origin_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], default='internal', string='Origin Type')

    @api.constrains('work_email', 'work_phone', 'mobile_phone')
    def _check_contact_details(self):
        for rec in self:
            crm_lead_forensic.validate_email(rec.work_email)
            crm_lead_forensic.validate_phone(rec.work_phone)
            crm_lead_forensic.validate_phone(rec.mobile_phone)



class ResUsers(models.Model):
    _inherit = 'res.users'

    directorateofficer = fields.Boolean(string="Directorate Officer",default=False)
    position = fields.Selection(selection=[('ed','ED'),('nodal','Nodal'),('cdo','CDO')],string="Job Position")
    



    