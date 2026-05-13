# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InvestigationDirectorateDepartment(models.Model):
    _name = 'inv.dir.dept'
    _description = 'Investigation Directorate Department'

    investigation_id = fields.Many2one('project.project')
    directorate_id = fields.Many2one('forensic.directorate', string="Directorates")
    department_id = fields.Many2one('forensic.department', string="Departments")
    color = fields.Char(string="Color", compute="_compute_color", store=True)

    @api.depends('directorate_id')
    def _compute_color(self):
        for rec in self:
            if rec.directorate_id and rec.directorate_id.color:
                rec.color = rec.directorate_id.color

    @api.depends('directorate_id', 'department_id')
    def _compute_display_name(self):
        for record in self:
            if record.directorate_id and record.department_id:
                record.display_name = str(record.directorate_id.name) + ' : ' + str(record.department_id.name)
            else:
                record.display_name = "Unknown"

    @api.constrains('investigation_id', 'directorate_id', 'department_id')
    def _check_unique_directorate_department(self):
        for record in self:
            # Get all lines of this investigation excluding current
            existing_lines = self.search([
                ('investigation_id', '=', record.investigation_id.id),
                ('id', '!=', record.id),
                ('directorate_id', '=', record.directorate_id.id),
                ('department_id', '=', record.department_id.id),
            ])
            if existing_lines:
                raise ValidationError(
                    "You cannot have the same directorate and department combination\n"
                    "more than once in investigation directorate."
                )
