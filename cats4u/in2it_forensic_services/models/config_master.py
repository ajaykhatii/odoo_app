# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .crm_lead_forensic import get_financial_year
import logging
import re


_logger = logging.getLogger(__name__)


class NatureOfAllegation(models.Model):
    """Forensic Nature of Allegation"""
    _name = 'forensic.allegation.nature'
    _description = 'Forensic Nature of Allegation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Allegation", required=True, tracking=True)

class ForensicDirectorate(models.Model):
    """Forensic Directorate"""
    _name = 'forensic.directorate'
    _description = 'Forensic Directorate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Directorate", required=True, tracking=True)
    active = fields.Boolean(default=True)
    department_ids = fields.Many2many('forensic.department', 'directorate_department_rel', 'directorate_id', 'department_id', 'Departments', tracking=True)
    ed_officer_id = fields.Many2one('res.users')
    nodal_officer_ids = fields.Many2many('res.users', 'directorate_nodal_user_rel', 'directorate_id', 'user_id')

    _sql_constraints = [
        (
            'unique_directorate_name',
            'unique(name)',
            'Directorate name must be unique.'
        ),
    ]
    color = fields.Char(string="Tag Color", default="#3498db")

    @api.constrains('name')
    def _check_name_constraints(self):
        """
         Validations:
        - Name max length 100
        - No duplicate name (case-insensitive)
        - Allow A–Z, a–z, spaces and special characters
        """
        # Allow alphabets, spaces and special characters
        # Disallow digits only
        pattern = re.compile(r'^[A-Za-z\s\W]+$')

        for rec in self:
            if not rec.name:
                continue

            #  Max length check
            if len(rec.name) > 100:
                raise ValidationError(
                    _("Directorate name cannot exceed 100 characters.")
                )

            # Character validation
            if not pattern.match(rec.name):
                raise ValidationError(
                    _("Directorate name can contain only alphabets, spaces "
                      "and special characters. Numbers are not allowed.")
                )

            # Duplicate check (case-insensitive)
            duplicate = self.search([
                ('id', '!=', rec.id),
                ('name', '=ilike', rec.name)
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    _("Directorate name '%s' already exists.") % rec.name
                )


class ForensicDepartment(models.Model):
    """Forensic Department"""
    _name = 'forensic.department'
    _description = 'Forensic Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Department", required=True, tracking=True)
    active = fields.Boolean(default=True)
    directorate_ids = fields.Many2many('forensic.directorate', 'directorate_department_rel', 'department_id', 'directorate_id',
                                      'Directorates', tracking=True)

    _sql_constraints = [
        (
            'unique_department_name',
            'unique(name)',
            'Department name must be unique.'
        ),
    ]

    @api.constrains('name')
    def _check_name_constraints(self):
        """
         Validations:
        - Name max length 100
        - No duplicate name (case-insensitive)
        - Allow A–Z, a–z, spaces and special characters
        """
        # Allow alphabets, spaces and special characters
        # Disallow digits only
        pattern = re.compile(r'^[A-Za-z\s\W]+$')

        for rec in self:
            if not rec.name:
                continue

            #  Max length check
            if len(rec.name) > 100:
                raise ValidationError(
                    _("Department name cannot exceed 100 characters.")
                )

            # Character validation
            if not pattern.match(rec.name):
                raise ValidationError(
                    _("Department name can contain only alphabets, spaces "
                      "and special characters. Numbers are not allowed.")
                )

            # Duplicate check (case-insensitive)
            duplicate = self.search([
                ('id', '!=', rec.id),
                ('name', '=ilike', rec.name)
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    _("Department name '%s' already exists.") % rec.name
                )


class ForensicAssignmentStage(models.Model):
    """Forensic Case Assignment Stage"""
    _name = 'forensic.assignment.stage'
    _description = 'Forensic Case Assignment Stage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "sequence, id"

    name = fields.Char(string="Name", required=True, tracking=True)
    active = fields.Boolean(default=True,  tracking=True)
    is_common_stage = fields.Boolean("Is Internal?",default=False, tracking=True)
    is_under_review = fields.Boolean("Is Reviewed?", default=False, tracking=True,
                                     help="Stage used for committee actions to review and assign cases onward.")
    sequence = fields.Integer(default=10, tracking=True)
    type_ids = fields.Many2many('forensic.assignment.type', 'assignment_type_stage_rel',
                                'stage_id', 'type_id', string="Assignment Types", tracking=True)
    description = fields.Text('Description', tracking=True)
    is_last = fields.Boolean("Is Last", tracking=True)

    @api.onchange('is_last')
    def _onchange_stage(self):
        for rec in self:
            if rec.is_last:
                duplicate = self.search([('is_last','=',True),('id','!=',rec._origin.id)], limit=1)
                if duplicate:
                    raise UserError(f"Only one 'Last' stage can be configured.")

    @api.onchange('is_common_stage')
    def _onchange_common_stage(self):
        for rec in self:
            if not rec.is_common_stage:
                rec.is_under_review = False

    def action_view_assignment_types(self):
        """Smart button: show Assignment Types linked to this Stage"""
        self.ensure_one()

        return {
            'name': 'Assignment Types',
            'type': 'ir.actions.act_window',
            'res_model': 'forensic.assignment.type',
            'view_mode': 'list',
            'target': 'current',
            'domain': [('stage_ids', 'in', [self.id])],
            'context': {
                'default_stage_ids': [(6, 0, [self.id])],
                'create': False,
            },
        }

    @api.constrains('is_common_stage', 'is_under_review')
    def _ensure_minimum_stage_types(self):
        """
           Ensure:
           1. At least one stage must have is_common_stage = True
           2. At least one stage must have is_under_review = True
           """
        for rec in self:
            # If user is trying to set it to False
            if not rec.is_common_stage:
                common_count = self.search_count([('is_common_stage', '=', True)])
                # If there is only one common stage left AND it is this record → prevent unchecking
                if common_count == 0:
                    raise ValidationError("At least one stage must be marked as a internal stage.")

            if not rec.is_under_review:
                under_review_count = self.search_count([('is_under_review', '=', True)])
                if under_review_count == 0:
                    raise ValidationError("At least one stage must be marked as a under review.")



class ForensicAssignmentType(models.Model):
    """Forensic Case Assignment Type"""
    _name = 'forensic.assignment.type'
    _description = 'Forensic Case Assignment Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Short Name", required=True, tracking=True)
    complete_name = fields.Char(string="Name", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    stage_ids = fields.Many2many('forensic.assignment.stage', 'assignment_type_stage_rel',
                                 'type_id', 'stage_id', string="Stages", tracking=True)
    is_authorize = fields.Boolean("Is Authorize?")
    auth_template_id = fields.Many2one(
        string='Template',
        comodel_name='ir.ui.view',
        ondelete='restrict',
    )
    authority_id = fields.Many2one('hr.job', string='Auth Ownership')

    # TODO: On change of financial year, the old year needs to be created and mapped manually.
    #  The new one will be synced automatically.
    sequence_id = fields.Many2one('ir.sequence', string='Sequence', tracking=True)

    # ------------------------------------------------------
    # Generate unique sequence per assignment type + FY
    # ------------------------------------------------------
    @api.model
    def _generate_case_number(self):
        # Convert name to uppercase first 3 chars
        case_specific = (self.name or '').upper()[:3]

        fy = get_financial_year(self.env)        # eg: "25-26"

        # Unique sequence CODE per assignment type per financial year
        seq_code = f"forensic.{case_specific.lower()}.case.{fy}"
        seq = self.env['ir.sequence'].sudo().search(
            [('code', '=', seq_code)], limit=1)
        if not seq:
            seq = self.env['ir.sequence'].sudo().create({
                'name': f"Forensic {case_specific} Case {fy}",
                'code': seq_code,
                'padding': 3,
                'prefix': f"EFS/{case_specific}/",
                'number_next_actual': 1,
            })
        return seq

    def generate_case_type_sequence(self):
        for rec in self:
            if not rec.sequence_id:
                rec.sequence_id = rec._generate_case_number()

class ForensicAllegationSource(models.Model):
    """Forensic Allegation Source"""
    _name = 'forensic.allegation.source'
    _description = 'Forensic Allegation Source'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Source Name", required=True, tracking=True)
    active = fields.Boolean(default=True)

