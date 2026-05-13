# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api



class AssignProjectManagerWizard(models.TransientModel):
    _name = 'assign.project.manager.wizard'
    _description = 'Assign Project Manager Wizard'

    user_id = fields.Many2one('res.users', string="Investigation Manager", required=True)

    manager_ids = fields.Many2many(
        'res.users',
        string="Allowed Managers",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # Your business logic
        manager_users = self.env['hr.department'].search(
            [('manager_id', '!=', False)]
        ).mapped('manager_id.user_id')

        res['manager_ids'] = [(6, 0, manager_users.ids)]

        return res


    def action_assign_pm(self):
        active_ids = self.env.context.get('active_ids', [])
        projects = self.env['project.project'].browse(active_ids)
        projects.write({'user_id': self.user_id.id})
