# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
import json
from odoo.exceptions import UserError, ValidationError


class AssignedForensicTeam(models.Model):
    _name = 'assigned.forensic.team'
    _description = 'Assigned Team'
    _rec_name = 'project_id'
    _inherit = ['mail.thread','mail.activity.mixin']

    project_id = fields.Many2one('project.project', string="Investigation", tracking=True)
    project_investigator_ids = fields.Many2many(
        'res.users', string='Lead Investigator',
        help='Investigator must be selected from investigation team members only.', tracking=True)
    
    forensic_member_ids = fields.One2many(
        comodel_name='forensic.investigation.team',
        inverse_name='assign_forensic_team_id',
        string="Investigation Members",
        help='List of investigation members linked to this case.'
        , tracking=True
    )
    report_review_status = fields.Selection(related='project_id.report_review_status')

    investigator_domain = fields.Char(string="Investigation Domain", compute="_compute_investigation_ids")

    def _compute_investigation_ids(self):
        for rec in self:
            rec.investigator_domain = False
            if rec.forensic_member_ids:
                rec.investigator_domain = json.dumps([('id', 'in', [rec.forensic_member_ids.mapped('member_ids')])])

    record_access = fields.Selection(related="project_id.record_access")


    li_domain = fields.Char(compute="_compute_li_domain")
    is_investigation_manager = fields.Boolean(compute='_is_investigation_manager')
    change_request_count = fields.Integer(compute="_compute_change_request_count")
    approved_change_request_count = fields.Integer(compute="_compute_change_request_count")

    def _compute_change_request_count(self):
        for rec in self:
            rec.change_request_count = self.env['team.change.request'].search_count([('team_id', '=', self.id)])
            rec.approved_change_request_count = self.env['team.change.request'].search_count([
                ('team_id', '=', self.id),
                ('state', 'in', ['approved', 'rejected']),
            ])

    @api.depends('project_id')
    def _is_investigation_manager(self):
        is_admin = self.env.user.has_group('base.group_system')
        is_fcm_admin = self.env.user.has_group('in2it_forensic_services.group_fcm_admin')
        for rec in self:
            rec.is_investigation_manager = False
            rec.is_investigation_manager = (
                    is_admin or is_fcm_admin or self.env.user == rec.project_id.user_id
            )

    @api.depends('forensic_member_ids')
    def _compute_li_domain(self):
        for rec in self:
            rec.li_domain = json.dumps([('id','=',False)])
            if rec.forensic_member_ids:
                ids_list = rec.forensic_member_ids.mapped('member_ids').ids
                rec.li_domain = json.dumps([('id', 'in', ids_list)])

    def unlink(self):
        if not self.env.user.has_group('base.group_system'):
            raise UserError("Only System Administrator can delete this record.")
        return super().unlink()
    
    @api.constrains('project_id', 'project_investigator_ids', 'forensic_member_ids')
    def _check_manager_investigators(self):
        for rec in self:
            forensic_mem_ids = rec.forensic_member_ids.mapped('member_ids').ids
            if rec.project_id.user_id and forensic_mem_ids:
                if rec.project_id.user_id.id in forensic_mem_ids:
                    raise ValidationError("Investigation manager cannot be a part of Investigation Team.")
                

    @api.constrains('forensic_member_ids')
    def _check_investigation_member(self):
        for rec in self:

            if not rec.project_investigator_ids:
                raise ValidationError("Forensic Team Required.")
            # -------------------------------
            # Remove invalid lead investigators
            # -------------------------------
            #  invalid_leads means members who is removed from investigation line but set as let investigator
            valid_members = rec.project_id.assigned_forensic_team_id.forensic_member_ids.mapped('member_ids')
            invalid_leads = rec.project_id.assigned_forensic_team_id.project_investigator_ids - valid_members

            if invalid_leads:
                raise ValidationError(_(f"{', '.join(invalid_leads.mapped('name'))} member is part of the Lead Investigator Team. \nRemove them from Lead Investigator first."))
            

            manager_id = self.env.ref('in2it_forensic_services.manager')
            pfo_id = self.env.ref('in2it_forensic_services.principle_of_forensic_officer')

            job_id_manager_count = 0
            job_id_pfo_count = 0
            for team in self.forensic_member_ids:
                investigation_team = self.env['forensic.investigation.team'].search(
                    [('id', '!=', team.id),('assign_forensic_team_id','=',team.assign_forensic_team_id.id), ('project_id', '=', rec.project_id.id), ('job_id', '=', team.job_id.id),
                     ('unit_id', '=', team.unit_id.id)])
                
                if investigation_team:
                    raise ValidationError(f'Unit with job position already exist!')
                manager_count = 0
                pfo_count = 0
                for member in team.member_ids:
                    if member.employee_id.job_id == self.env.ref('in2it_forensic_services.manager'):
                        manager_count += 1

                    if member.employee_id.job_id == self.env.ref(
                            'in2it_forensic_services.principle_of_forensic_officer'):
                        pfo_count += 1

                if (manager_count or pfo_count) > 1:
                    raise ValidationError("\n\n You can select one PFO / Manager.")

                if team.job_id == manager_id:
                    job_id_manager_count += 1

                if job_id_manager_count > 1:
                    raise ValidationError("You can assign only one Manager for this record.")

                if team.job_id == pfo_id:
                    job_id_pfo_count += 1

                if job_id_pfo_count > 1:
                    raise ValidationError("You can assign only one PFO for this record.")

            if not job_id_pfo_count:
                raise ValidationError("At least one PFO is required to create investigation team.")


    def write(self, vals):

        # Store old data before write
        old_forensic = {rec.id: rec.forensic_member_ids.mapped('member_ids') for rec in self}
        old_li = {rec.id: rec.project_investigator_ids for rec in self}

        res = super().write(vals)

        template = self.env.ref(
            'in2it_project_management.mail_template_investigation_team_assignment',
            raise_if_not_found=False
        )

        for rec in self:
            emails = []

            # New forensic members
            if 'forensic_member_ids' in vals:
                new_members = rec.forensic_member_ids.mapped('member_ids')
                added = new_members - old_forensic.get(rec.id, self.env['res.users'])
                emails += [u.email for u in added if u.email]

            # New investigators
            if 'project_investigator_ids' in vals:
                new_li = rec.project_investigator_ids
                added = new_li - old_li.get(rec.id, self.env['res.users'])
                emails += [u.email for u in added if u.email]

            if emails and template:
                template.send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'email_to': ",".join(set(emails))}
                )

        return res

    def action_open_change_request_wizard(self):
        return {
            'name': 'Team Change Request',
            'type': 'ir.actions.act_window',
            'res_model': 'team.change.request',
            'view_mode': 'form',
            'view_id': self.env.ref('in2it_project_management.team_change_request_wizard_view_form').id,
            'target': 'new',
            'context': {
                'default_team_id': self.id,
                'default_change_type': 'member',
                'team_line_ids': self.forensic_member_ids.ids
            }
        }

    def action_team_change_request_approval(self):
        list_view = self.env.ref('in2it_project_management.team_change_request_tree').id
        return {
            'name': _("Team Change Request"),
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'view_id': list_view,
            'res_model': 'team.change.request',
            'domain': [('team_id', '=', self.id)],
            'context': {'search_default_pending': 1,
                        'search_default_group_by_project':1
                        }
        }
