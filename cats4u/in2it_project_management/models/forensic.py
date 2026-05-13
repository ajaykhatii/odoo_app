# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class InheritComplaintPhysicalItem(models.Model):
    _inherit = 'complaint.physical.item'

    project_id = fields.Many2one(
        'project.project',
        string="Project",
        ondelete='cascade',
        tracking=True,
    )

    doc_type_id = fields.Many2one("forensic.document.type",string="Document Type", tracking=True)
    is_exhibit = fields.Boolean(string="Is Exhibit", tracking=True)

class InheritForensicCaseSuspects(models.Model):
    _inherit = 'forensic.case.suspects'
    
    project_id = fields.Many2one(
        'project.project',
        string="Project",
        ondelete='cascade',
        tracking=True,
    )

    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            if record.project_id:
                record.display_name = record.name
    
class InheritForensicInvestigationTeam(models.Model):
    """Used to assign member to a particular team"""
    _inherit = 'forensic.investigation.team'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    assign_forensic_team_id = fields.Many2one('assigned.forensic.team', string="Assign Team")

    @api.depends('unit_id','job_id')
    def _compute_display_name(self):
        for record in self:
            if record.unit_id and record.job_id:
                record.display_name = f"{record.unit_id.name} ({record.job_id.name})"

class InheritCaseType(models.Model):
    _inherit = 'forensic.assignment.type'

    is_project_create = fields.Boolean(string='Create Project')


class InheritForensicCaseAssignment(models.Model):
    _inherit = 'forensic.case.assignment'

    project_count = fields.Integer(string="Project", compute="_action_compute_project")
    assignment_stage = fields.Selection(
        string='Stages',
        selection=[('closed', 'Closed')]
    )
    closure_response = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="LIN Response")

    closure_comment = fields.Text(string="Closure Comment")

    def action_show_line_report(self):
        self.ensure_one()

        if not self.file_data:
            return

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/file_data/{self.file_name}?download=false',
            'target': 'new',
        }

    def action_open_comment_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Comment',
            'res_model': 'comment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_id': self.id,
                'default_model': self._name,
            }
        }

    def action_close_case(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Close Case',
            'res_model': 'forensic.case.close.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_case_id': self.id,
            }
        }

    def _action_compute_project(self):
        for rec in self:
            project = self.env['project.project'].search_count([('assignment_id','=',rec.id)])
            if project:
                rec.project_count = project
            else:
                rec.project_count = 0

    def action_open_case_assignment_model(self):
        return {
            'name': _("Project"),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'project.project',
            'domain': [('assignment_id', '=', self.id)],
            'context': {
                'create': False,
                'edit': False,
            }
        }
    

class InheritCaseIntake(models.Model):
    _inherit = 'crm.lead'

    project_count = fields.Integer(string="Project", compute="_action_compute_project")

    def _action_compute_project(self):
        for rec in self:
            project = self.env['project.project'].search_count([('case_id','=',rec.id)])
            if project:
                rec.project_count = project
            else:
                rec.project_count = 0

    def action_open_case_assignment_model(self):
        return {
            'name': _("Project"),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'project.project',
            'domain': [('case_id', '=', self.id)],
            'context': {
                'create': False,
                'edit': False,
            }
        }
    


class InheritForensicDocumentLine(models.Model):
    _inherit = 'forensic.document.line'

    project_id = fields.Many2one('project.project', string="Project")



class InheritForensicCaseWitness(models.Model):
    _inherit = 'forensic.case.witness'
    
    project_id = fields.Many2one(
        'project.project',
        string="Project",
        ondelete='cascade',
        tracking=True,
    )
