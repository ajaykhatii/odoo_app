# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################


from odoo import models, fields, api, _

class ResourceCalendarInherited(models.Model):
    _inherit = "resource.calendar"

    associated_leaves_count = fields.Integer("Time Off Count", default="0", compute='_compute_associated_leaves_count')

    def _compute_associated_leaves_count(self):
        for rec in self:
            leaves_count = self.env['in2it.public.holidays'].search_count([('calendar_id','=', self.id)])
            rec.associated_leaves_count = leaves_count

    def action_public_holdays(self):
        "This Method is used to show the public holidays."
        return {
            'type': 'ir.actions.act_window',
            'name': 'Public Holidays',
            'res_model': 'in2it.public.holidays',
            'view_mode': 'list',
            'target': 'current',
            'context': {'default_calendar_id': self.id,
                        'default_date_from': fields.date.today(),
                        'default_date_to': fields.date.today()},
            'domain': [('calendar_id','=', self.id)],
        }