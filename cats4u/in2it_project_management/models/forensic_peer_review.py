# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError


class ForensicPeerReview(models.Model):
    _name = 'forensic.peer.review'
    _description = 'Forensic Peer Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'project_id'

    project_id = fields.Many2one('project.project', string='Investigation', required=True)
    is_valid_reviewers = fields.Boolean('Is Valid Reviewer', compute='_compute_is_valid_peer_reviewer')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('complete', 'Complete')
    ], default='pending', tracking=True)
    line_ids = fields.One2many(
        'forensic.peer.review.line',
        'review_id'
    )

    pending_approved_line_ids = fields.One2many(
        'forensic.peer.review.line',
        'review_id',
        string="Pending / Approved Actions",
        domain=[('action', 'in', ['pending', 'approved'])]
    )

    changes_line_ids = fields.One2many(
        'forensic.peer.review.line',
        'review_id',
        string="Changes Requested",
        domain=[('action', '=', 'changes_required')]
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="ED Approval Docs", tracking=True
    )

    signature = fields.Binary(string="Signature")
    is_manager = fields.Boolean(compute="_compute_is_manager")
    can_sign = fields.Boolean(compute="_compute_can_sign")
    is_review_complete = fields.Boolean(string="Is Review Complete")
    case_type = fields.Selection(related='project_id.case_type', string="Case Type")
    sign_off_date = fields.Date("Sign Off Date")
    assignment_type = fields.Selection(related="project_id.assignment_type", string="Case Handling Type", tracking=True)
    is_external_report_submitted = fields.Boolean(related="project_id.is_external_report_submitted", string="Is External Report Submitted")

    def _compute_is_manager(self):
        for rec in self:
            rec.is_manager = rec.project_id.user_id == self.env.user

    @api.depends('attachment_ids')
    def _compute_can_sign(self):
        for rec in self:
            rec.can_sign = bool(rec.attachment_ids)

    def _send_review_notifications(self):
        """Send notification based on line action"""
        notification_model = self.env['system.notification']
        if self.assignment_type == 'internal':
            res_model = self.env['ir.model']._get(self._name)

            for rec in self:
                for line in rec.line_ids:

                    notify_users = []
                    # Pending → notify reviewer
                    if line.action == 'pending' and line.user_id:
                        notify_users.append(line.user_id)

                    # Changes Required → notify previous reviewer
                    elif line.action == 'changes_required' and line.previous_reviewer_id:
                        notify_users.append(line.previous_reviewer_id)
                    # skip if no users
                    if not notify_users:
                        continue

                    message = f"Report Awaiting Review – Investigation Report for {rec.project_id.name} submitted."
                    for user in notify_users:
                        # Check if already notified
                        existing = notification_model.search([
                            ('user_id', '=', user.id),
                            ('res_id', '=', rec.id)
                        ], limit=1)

                        if existing:
                            continue  # skip duplicate

                        notification_model.create({
                            'message': message,
                            'user_id': user.id,
                            'res_model_id': res_model.id if res_model else False,
                            'res_id': rec.id
                        })
        else:
            model = self.project_id._name
            if model:
                res_model_id = self.env['ir.model'].search([('model','=',model)])
            if res_model_id:
                notification_model.create({
                    'message':f"Action required on Peer Review for project {self.project_id.name}",
                    'user_id': self.project_id.assigned_pfo_id.id,
                    "res_model_id": res_model_id.id or False,
                    "res_id": self.project_id.id,
                })

    @api.depends('line_ids.user_id', 'line_ids.action')
    def _compute_is_valid_peer_reviewer(self):
        for rec in self:
            user_lines = rec.line_ids.filtered(
                lambda l: l.user_id == self.env.user
            )

            # if user already approved any line → hide buttons
            if any(l.action == 'approved' for l in user_lines):
                rec.is_valid_reviewers = False
            else:
                rec.is_valid_reviewers = any(
                    l.action in ('pending', 'changes_required')
                    for l in user_lines
                )

    def action_approve(self):
        self.ensure_one()
        if self.project_id.assignment_type == 'external':
            user_lines = self.line_ids.filtered(lambda l: l.user_id == self.env.user)
            pending_line = user_lines.filtered(lambda l: l.action == 'pending')
            if pending_line:
                line = pending_line[0]
                line.write({
                    'action': 'approved',
                    'date': fields.Datetime.now()
                })
            self.write({'state': 'complete','sign_off_date': fields.date.today()})
            self.project_id._move_project_stage()
            return

        # Handle current user's approval
        user_lines = self.line_ids.filtered(lambda l: l.user_id == self.env.user)
        pending_line = user_lines.filtered(lambda l: l.action == 'pending')
        if pending_line:
            line = pending_line[0]
            line.write({
                'action': 'approved',
                'date': fields.Datetime.now()
            })
        else:
            last_line = user_lines.sorted('date')[-1]
            line = self.env['forensic.peer.review.line'].create({
                'review_id': self.id,
                'user_id': self.env.user.id,
                'action': 'approved',
                'previous_reviewer_id': last_line.previous_reviewer_id.id,
                'date': fields.Datetime.now()
            })
        self.write({'state': 'in_progress'})

        # Get forensic hierarchy
        team = self.project_id.assigned_forensic_team_id

        members = team.forensic_member_ids.sorted(
            key=lambda m: m.job_id.sequence or 0,
            reverse=True
        )
        current_member_line = members.filtered(
            lambda m: self.env.user in m.member_ids
        )

        # If user is part of forensic hierarchy
        if current_member_line:
            current_member_line = current_member_line[0]
            current_index = members.ids.index(current_member_line.id)

            current_level_users = current_member_line.member_ids

            # Check ALL users at this level approved
            for user in current_level_users:
                user_latest_line = self.line_ids.filtered(
                    lambda l: l.user_id == user
                ).sorted('date')[-1]

                if user_latest_line.action != 'approved':
                    return  # stop progression

            # Move to next forensic hierarchy
            if current_index + 1 < len(members):
                next_member = members[current_index + 1]
                for user in next_member.member_ids:
                    existing_pending = self.line_ids.filtered(
                        lambda l: l.user_id == user and l.action == 'pending'
                    )

                    if not existing_pending:
                        self.env['forensic.peer.review.line'].create({
                            'review_id': self.id,
                            'user_id': user.id,
                            'action': 'pending',
                            'previous_reviewer_id': self.env.user.id
                        })
                    self._send_review_notifications()
                return

        # AFTER forensic investigation hierarchy -> Manager -> Chief -> Complete
        project = self.project_id

        # Investigation Manager
        if project.user_id:
            manager_latest = self.line_ids.filtered(
                lambda l: l.user_id == project.user_id
            )

            if not manager_latest:
                self.env['forensic.peer.review.line'].create({
                    'review_id': self.id,
                    'user_id': project.user_id.id,
                    'action': 'pending',
                    'previous_reviewer_id': self.env.user.id
                })
                self._send_review_notifications()
                return
            else:
                manager_latest = manager_latest.sorted('date')[-1]
                if manager_latest.action != 'approved':
                    return

        # Chief
        if project.chief_id:
            chief_latest = self.line_ids.filtered(
                lambda l: l.user_id == project.chief_id
            )

            if not chief_latest:
                self.env['forensic.peer.review.line'].create({
                    'review_id': self.id,
                    'user_id': project.chief_id.id,
                    'action': 'pending',
                    'previous_reviewer_id': self.env.user.id
                })
                self._send_review_notifications()
                return
            else:
                chief_latest = chief_latest.sorted('date')[-1]
                if chief_latest.action != 'approved':
                    return


        # System Notification
        res_model_id = self.env['ir.model'].search([('model', '=', 'forensic.peer.review')])
        if res_model_id:
            self.env['system.notification'].create({
                'message': f"Report Awaiting Sign Off – Investigation Report for Investigation {self.project_id.name}.",
                'user_id': self.project_id.user_id.id,
                "res_model_id": res_model_id.id or False,
                "res_id": self.id
            })
        # Final state
        self.is_review_complete = True


    def action_changes_required(self):
        self.ensure_one()
        return {
            'name': 'Changes Required',
            'type': 'ir.actions.act_window',
            'res_model': 'peer.review.change.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id
            }
        }

    def action_open_signoff_wizard(self):
        self.ensure_one()

        if self.env.user != self.project_id.user_id:
            raise UserError("Only Investigation Manager can sign off.")

        if not self.is_review_complete:
            raise UserError("Review must be completed first.")

        if not self.project_id.distribution_line_ids:
            raise ValidationError("Please create distribution list before proceeding.")

        # validation for atleast one ED in distribution list
        ed_users = self.project_id.distribution_line_ids.mapped('user_id').filtered(
            lambda u: u.position == 'ed'
        )
        if not ed_users:
            raise ValidationError("At least one ED must be in the distribution list.")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sign Off Review',
            'res_model': 'peer.review.signoff.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_id': self.id
            }
        }

    def action_preview_investigation_report(self):
        self.ensure_one()
        project = self.project_id
        if not project.distribution_line_ids:
            raise ValidationError("The distribution list is no longer available. Please recreate it or contact your administrator.")

        ed_users = self.project_id.distribution_line_ids.mapped('user_id').filtered(
            lambda u: u.position == 'ed'
        )
        if not ed_users:
            raise ValidationError("At least one ED must be in the distribution list.")

        return self.env.ref(
            'in2it_project_management.action_investigation_report'
        ).report_action(self.project_id)

    def action_preview_preliminary_report(self):
        self.ensure_one()
        return self.env.ref('in2it_project_management.action_pre_investigation_report').report_action(self.project_id)

    @api.constrains('signature')
    def _check_manager_signature(self):
        for rec in self:
            if rec.signature and self.env.user != rec.project_id.user_id:
                raise ValidationError("Only Investigation Manager can sign.")


class ForensicPeerReviewLine(models.Model):
    _name = 'forensic.peer.review.line'
    _description = 'Peer Review Line Comment'
    _order = "date asc, id asc"

    review_id = fields.Many2one(
        'forensic.peer.review',
        string="Peer Review",
        ondelete='cascade'
    )
    user_id = fields.Many2one(
        'res.users',
        string="Approver",
        required=True
    )
    job_id = fields.Many2one(
        'hr.job',
        string="Job Position",
        related='user_id.employee_id.job_id',
        store=True,
        readonly=True
    )
    action = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('changes_required', 'Changes Required')
    ], string="Status")

    previous_reviewer_id = fields.Many2one('res.users', 'Requested User')
    comment = fields.Text(string="Comment")
    date = fields.Datetime(string="Date")
