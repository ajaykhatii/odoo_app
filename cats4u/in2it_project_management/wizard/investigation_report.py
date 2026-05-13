from odoo import api, models, fields
from odoo.exceptions import ValidationError


class DistributionLine(models.Model):
    _name = 'distribution.line'
    _description = 'Distribution Line'
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users',string="User", domain="[('id', 'in', allowed_user_ids)]")
    active = fields.Boolean(default=True)
    action = fields.Selection([('info', 'Information'), ('action', 'Action')], string="Action")
    project_id = fields.Many2one('project.project',string="Investigation")
    memo_id = fields.Many2one('overarching.memo',string="Overarching memo")
    status = fields.Selection([('pending', 'Pending'), ('approved', 'Approved')], default="pending",string="Status")
    is_lead_investigator = fields.Boolean(string="Is Lead Investigator", compute="_check_lead_investigator", store=True)

    allowed_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_allowed_user_ids',
        store=False
    )

    def _check_lead_investigator(self):
        # allow LI/PFO/FCM Admin/Admin to set distribution list if peer review not done
        is_admin = self.env.user.has_group('base.group_system')
        is_fcm_admin = self.env.user.has_group('in2it_forensic_services.group_fcm_admin')
        for rec in self:
            rec.is_lead_investigator = False
            rec.is_lead_investigator = (
                    is_admin or
                    is_fcm_admin or
                    self.env.user in rec.project_id.assigned_forensic_team_id.project_investigator_ids or
                    self.env.user == rec.project_id.assigned_pfo_id
            )

    @api.depends('project_id')
    def _compute_allowed_user_ids(self):
        Users = self.env['res.users']
        city_manager_group = self.env.ref(
            'in2it_forensic_services.group_fcm_city_manager',
            raise_if_not_found=False
        )
        chief_group = self.env.ref(
            'in2it_forensic_services.group_fcm_case_chief_access',
            raise_if_not_found=False
        )

        for rec in self:
            allowed_users = Users.browse()

            if not rec.project_id:
                rec.allowed_user_ids = allowed_users
                continue

            # Already selected users in this project
            existing_users = rec.project_id.distribution_line_ids.mapped('user_id')
            if rec.user_id:
                existing_users = existing_users - rec.user_id

            # ED users
            ed_users = Users.search([
                ('directorateofficer', '=', True),
                ('position', '=', 'ed')
            ])

            # City Managers
            city_users = city_manager_group.users if city_manager_group else Users.browse()

            # Chief group users
            chief_users = chief_group.users if chief_group else Users.browse()
            # Merge all
            allowed_users = ed_users | city_users | chief_users
            allowed_users -= existing_users
            rec.allowed_user_ids = allowed_users

    @api.model
    def create(self, vals):
        project = self.env['project.project'].browse(vals.get('project_id'))
        if project and project.report_review_status == 'completed':
            raise ValidationError(
                "You cannot create distribution list because the peer review is completed."
            )
        return super().create(vals)

    def write(self, vals):
        for rec in self:
            project = rec.project_id
            # also handle case when project_id is being changed
            if vals.get('project_id'):
                project = self.env['project.project'].browse(vals.get('project_id'))
            if project and project.report_review_status == 'completed':
                raise ValidationError(
                    "You cannot modify distribution list because the peer review is completed."
                )

        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.project_id and rec.project_id.report_review_status == 'completed':
                raise ValidationError(
                    "You cannot delete distribution list because the peer review is completed."
                )

        return super().unlink()

    @api.constrains('user_id', 'project_id')
    def _check_unique_user_per_project(self):
        for rec in self:
            if not rec.user_id or not rec.project_id:
                continue

            domain = [
                ('user_id', '=', rec.user_id.id),
                ('project_id', '=', rec.project_id.id),
                ('id', '!=', rec.id),
            ]

            if self.search_count(domain):
                raise ValidationError(
                    "This user is already assigned in this distribution list."
                )

