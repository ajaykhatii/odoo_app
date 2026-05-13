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

class AssignStandardTaskWizard(models.TransientModel):
    _name = "assign.standard.task.wizard"
    _description = "Assign Standard Task Wizard"

    assign_standard_task_ids = fields.Many2many("standard.task", string="Standard Tasks", required=True)
    project_id = fields.Many2one("project.project",string="Project")

    def action_Assign_standard_task(self):
        for rec in self:
            if rec.assign_standard_task_ids:
                for st_task in rec.assign_standard_task_ids:
                    vals = {
                        'project_id': self.project_id.id,
                        'name': st_task.name,
                        'task_category_id': st_task.task_category_id.id,
                        'task_details': st_task.task_details,
                        'is_sla': st_task.is_sla,
                        'sla_days': st_task.sla_days,
                        'stage_id': self.env.ref('in2it_project_management.project_task_stage_draft').id,
                    }
                    self.env['project.task'].sudo().create(vals)
                rec.project_id.is_create_task = True
