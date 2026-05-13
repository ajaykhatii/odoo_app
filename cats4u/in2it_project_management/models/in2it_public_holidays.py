# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################


from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, AccessError


class In2itPublicHolidays(models.Model):
    _name = "in2it.public.holidays"
    _description = "Public Holidays"

    name = fields.Char("Name", required=True)
    date_from = fields.Date("Start Date")
    date_to = fields.Date("End Date")
    calendar_id = fields.Many2one("resource.calendar", string="Working Hours")

    @api.constrains('date_from', 'date_to', 'calendar_id')
    def _check_duplicate_dates(self):
        for record in self:

            if record.date_from > record.date_to:
                raise ValidationError("Start Date cannot be after End Date.")

            domain = [
                ('id', '!=', record.id),
                ('calendar_id', '=', record.calendar_id.id),
                ('date_from', '<=', record.date_to),
                ('date_to', '>=', record.date_from),
            ]

            overlapping = self.search(domain, limit=1)

            if overlapping:
                raise ValidationError(
                    "A public holiday already exists within this date range for the selected calendar."
                )