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

class StandardTaskCategory(models.Model):
    _name = "standard.task.category"
    _description = "Standard Task Category"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", tracking=True, required=True)


class StandardTask(models.Model):
    _name = "standard.task"
    _description = "Standard Tasks"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", tracking=True, required=True)
    task_details = fields.Char(string="Task Details")
    task_category_id = fields.Many2one("standard.task.category", string="Task Category",tracking=True)
    is_sla = fields.Selection([('yes','Yes'),('no','No')], default="no", string="SLA", tracking=True)
    sla_days = fields.Integer(string="SLA(in days)", tracking=True)

    @api.onchange('sla_days')
    def _onchange_sla_days(self):
        if self.sla_days < 0:
            raise ValidationError("SLA should be Positve.")


