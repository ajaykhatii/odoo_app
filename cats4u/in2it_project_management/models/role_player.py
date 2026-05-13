from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class ProjectRole(models.Model):
    _name = 'project.role'
    _description = 'Project Role'
    _order = 'role_id'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        ondelete='cascade'
    )
    role_id = fields.Many2one(
        'role.player.abbreviation',
        string='Abbreviation',
        required=True,
        ondelete='cascade'
    )
    description = fields.Char("Description",
        related='role_id.description',
        readonly=True,
        store=True
    )
    active = fields.Boolean(default=True)


    _sql_constraints = [
        ('unique_role_per_project', 'unique(project_id, role_id)', 'This role already exists.')
    ]

class RolePlayerAbbreviation(models.Model):
    _name = 'role.player.abbreviation'
    _description = 'Role Player Abbreviation'
    _order = 'name asc'
    _rec_name = 'name'

    name = fields.Char(
        string="Abbreviation",
        required=True,
        size=10
    )

    description = fields.Char(
        string="Description",
        required=True,
        size=50
    )

    is_seeded = fields.Boolean(
        string="Is Standard?",
        default=False
    )

    active = fields.Boolean(
        string="Active",
        default=True
    )

    
    
    _sql_constraints = [
        (
            'unique_name',
            'unique(name)',
            'Abbreviation must be unique (case-insensitive).'
        )
    ]

   
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].upper()
        return super().create(vals_list)
    

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super().write(vals)



    @api.constrains('name')
    def _check_abbreviation_format(self):
        for rec in self:
            if not rec.name:
                continue

            if not re.match(r'^[A-Z]+$', rec.name):
                raise ValidationError(
                    "Abbreviation must contain only uppercase letters (A-Z) "
                    "with no spaces or special characters."
                )

    # @api.constrains('description')
    # def _check_description_length(self):
    #     for rec in self:
    #         if rec.description and len(rec.description) > 50:
    #             raise ValidationError(
    #                 "Role Name must not exceed 50 characters."
    #             )

    def unlink(self):
        for rec in self:
            if rec.is_seeded:
                raise ValidationError(
                    "Seeded roles cannot be deleted. You may deactivate them instead."
                )
        return super().unlink()
