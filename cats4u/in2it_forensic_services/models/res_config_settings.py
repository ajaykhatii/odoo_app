# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

MONTHS = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),
]

class ResCompany(models.Model):
    _inherit = 'res.company'

    fy_start_date = fields.Date(string="Start Date")
    fy_end_date = fields.Date(string="End Date" )

    @api.constrains('fy_start_date', 'fy_end_date')
    def _check_fy_date_range(self):
        for rec in self:
            # Skip validation if fields are empty
            if not rec.fy_start_date or not rec.fy_end_date:
                continue

            # Validate: End date must be >= Start date
            if rec.fy_end_date < rec.fy_start_date:
                raise ValidationError(
                    "FY End Date cannot be earlier than FY Start Date."
                )

    def generate_case_type_sequence(self):
        forensic_assignment_type = self.env['forensic.assignment.type'].search([])

        if all(t.sequence_id for t in forensic_assignment_type):
                raise ValidationError("Sequence already generated for all case types.")

        for rec in forensic_assignment_type:
            if not rec.sequence_id:
                rec.sequence_id = rec._generate_case_number()

class ResGroupCMS(models.Model):
    _inherit = "res.groups"

    is_cms = fields.Boolean(string="Is CMS", default=False)


