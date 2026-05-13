# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TeamChangeRequest(models.Model):
    _name = 'team.change.request'
    _description = 'Investigation Team Change Request'

    team_id = fields.Many2one('assigned.forensic.team', required=True, ondelete='cascade')
    change_type = fields.Selection([
        ('unit', 'Unit'),
        ('member', 'Member')
    ], default='member', required=True)

    team_line_id = fields.Many2one('forensic.investigation.team', string="Unit")
    team_member_ids = fields.Many2many(related='team_line_id.member_ids', string="Team Members")
    member_ids = fields.Many2many('res.users', string="Members")
    approver_id = fields.Many2one('res.users', string="Approver")
    is_approver = fields.Boolean(default=False, compute='_compute_is_approver')

    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')

    def unlink(self):
        if not self.env.user.has_group('base.group_system') or not self.env.user.has_group('in2it_forensic_services.group_fcm_admin'):
            raise ValidationError("Only Administrator can delete this record.")
        return super().unlink()

    @api.depends('approver_id')
    def _compute_is_approver(self):
        for rec in self:
            rec.is_approver = self.env.user == rec.approver_id\
                            or self.env.user.has_group('base.group_system')\
                            or self.env.user.has_group('in2it_forensic_services.group_fcm_admin')

    @api.onchange('change_type')
    def onchange_change_type(self):
        self.team_line_id = False
        self.member_ids = False
        self.approver_id = False

    @api.onchange('team_line_id')
    def _onchange_unit_id(self):
        self.member_ids = False
        if self.change_type == 'member':
            self.approver_id = self.team_line_id.unit_id.manager_id.user_id
        elif self.change_type == 'unit':
            self.approver_id = self.team_id.project_id.chief_id

    @api.constrains('team_id', 'change_type', 'team_line_id', 'member_ids', 'state')
    def _check_duplicate_request(self):
        pfo_id = self.env.ref('in2it_forensic_services.principle_of_forensic_officer')
        for rec in self:
            if not rec.team_id or not rec.change_type:
                continue

            if rec.change_type == 'member':
                if not rec.team_line_id.unit_id.manager_id:
                    raise ValidationError(_('Unit Manager is not set for %s.') % rec.team_line_id.unit_id.name)
                if rec.change_type == 'unit':
                    if not rec.team_id.project_id.chief_id:
                        raise ValidationError(_('Chief is not set on Investigation.'))

            if self.team_line_id:
                if self.team_line_id.job_id == pfo_id:
                    raise ValidationError("PFO is required; removal is not allowed.")

                member_ids = self.member_ids if self.change_type == 'member' else self.team_line_id.member_ids
                if member_ids in self.team_id.project_investigator_ids:
                    raise ValidationError("Lead Investigation member removal is not allowed.")

            domain = [
                ('id', '!=', rec.id),
                ('team_id', '=', rec.team_id.id),
                ('change_type', '=', rec.change_type),
                ('state', '=', 'pending'),
                ('team_line_id', '=', rec.team_line_id.id),
            ]

            # Member-specific check
            if rec.change_type == 'member' and rec.member_ids:
                domain.append(('member_ids', 'in', rec.member_ids.ids))

            existing = self.sudo().search(domain, limit=1)

            if existing:
                raise ValidationError("A Change Request for the same already exists!")


    def action_approve_team_change(self):
        for rec in self:
            if not (rec.change_type or rec.team_line_id or rec.member_ids):
                continue

            if rec.change_type == 'member' and rec.team_line_id and rec.member_ids:
                for member in rec.member_ids:
                    if rec.team_line_id:
                        rec.team_line_id.sudo().write({'member_ids': [(3, member.id)]})

                if rec.team_line_id.assign_forensic_team_id:
                    member_names = ', '.join(rec.member_ids.mapped('name'))
                    rec.team_line_id.assign_forensic_team_id.sudo().message_post(
                        body=f"Members Removed: {member_names}"
                    )
                if not rec.team_line_id.member_ids:
                    rec.team_line_id.sudo().write({'assign_forensic_team_id': False})

            if rec.change_type == 'unit' and rec.team_line_id:
                if rec.team_line_id.assign_forensic_team_id:
                    rec.team_line_id.assign_forensic_team_id.sudo().message_post(
                        body=f"Unit Removed: {rec.team_line_id.unit_id.name}/{rec.team_line_id.job_id.name}"
                    )

                if rec.team_line_id:
                    rec.team_line_id.sudo().write({'assign_forensic_team_id': False})

            rec.state = 'approved'

    def action_reject_team_change(self):
        self.state = 'rejected'

    def get_team_change_request(self):
        user = self.env.user
        # Default: no records
        domain = [('id', '=', False)]
        if user.has_group('base.group_system') or user.has_group('in2it_forensic_services.group_fcm_admin'):
            domain = [] # show all records
        else:
            domain = [('approver_id', '=', user.id)]

        action = self.env.ref('in2it_project_management.action_investigation_team_change_request')
        action.sudo().write({'domain': domain})
        return {
            'name': _('Team Change Request'),
            'res_model': 'team.change.request',
            'type': 'ir.actions.act_window',
            'view_mode': 'list',
            'id': action.id,
            'domain': domain,
            'context': {'search_default_pending': 1,
                        'search_default_group_by_project':1
                        }
        }
