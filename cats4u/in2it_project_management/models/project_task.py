# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,AccessError,UserError
from dateutil.relativedelta import relativedelta


class ProjectTaskInherit(models.Model):
    _inherit = "project.task"

    task_category_id = fields.Many2one("standard.task.category", string="Task Category", tracking=True)
    is_sla = fields.Selection([('no','No'),('yes','Yes')],default="no", string="SLA", tracking=True)
    sla_days = fields.Integer(string="SLA(In Days)", tracking=True)
    actual_completion_date = fields.Date("Actual Completion Date", tracking=True)
    task_details = fields.Char(string="Task Details")
    related_user_ids = fields.Many2many("res.users",string="Related Investigator", compute="_compute_related_user_id")
    approved_by_id = fields.Many2one("res.users", string="Approved By", readonly=True)
    approved_date = fields.Datetime(string="Approved On", readonly=True)
    stage = fields.Selection([('new','New'),('in_progress','In Progress'),('closed','Closed')], default="new", string="State")
    priority = fields.Selection(selection_add=[('1', 'Medium'),('2', 'High'),], ondelete={'2': 'set default'})

    approval_status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('approved', 'Approved')
        ],
        compute="_compute_approval_status",
        inverse="_inverse_approval_status",
        store=True
    )

    @api.depends('project_id.approval_status')
    def _compute_approval_status(self):
        for task in self:
            task.approval_status = task.project_id.approval_status

    def _inverse_approval_status(self):
        for task in self:
            task.project_id.approval_status = task.approval_status

    def action_approve_task(self):
        project_id = False
        for task in self:
            if not project_id:
                project_id = task.project_id
            if task.project_id != project_id:
                raise ValidationError(
                    "You can approve the investigation plan for only one case at a time."
                )
            if task.approval_status != 'pending':
                raise ValidationError(
                    "Approval is allowed only when the investigation is in Pending status."
                )

        for task in self:
            if task.project_id.user_id != self.env.user:
                raise UserError(
                    "Only the assigned manager can approve this task."
                )

            stages = task.project_id.type_ids.sorted('sequence')
            if not stages:
                raise UserError(_("No stages configured for this project."))

            # Find current stage index
            try:
                current_index = stages.ids.index(task.stage_id.id)
            except ValueError:
                raise UserError(_("Current stage is not valid for this project."))

            # Check if already last stage
            if current_index + 1 >= len(stages):
                raise UserError(_("This task is already in the final stage."))

            # Move TASK to next stage
            next_stage = stages[current_index + 1]
            task.write({
                "approval_status": 'approved',
                "approved_by_id": self.env.user.id,
                "approved_date": fields.Datetime.now(),
                "stage_id": next_stage.id,
            })

        # Move PROJECT to next stage
        current_stage = project_id.stage_id
        if not current_stage:
            raise UserError(_("Project has no current stage."))

        # Find next stage strictly by sequence
        next_project_stage = self.env['project.project.stage'].search([
            ('sequence', '>', current_stage.sequence),
        ], order='sequence asc', limit=1)

        if next_project_stage:
            project_id.stage_id = next_project_stage.id

        model = 'project.project'
        if model:
            res_model_id = self.env['ir.model'].search([('model','=',model)])
        investigator = self.mapped('project_id.assigned_forensic_team_id.project_investigator_ids')
        for lead_investigator in investigator:
            if res_model_id:
                self.env['system.notification'].create({
                    'message':f"Investigation Plan for Case {self.project_id.name} is Approved.",
                    'user_id':lead_investigator.id,
                    "res_model_id":res_model_id.id or False,
                    "res_id":self.project_id.id
                })
                
        return True
    
    @api.depends('project_id')
    def _compute_related_user_id(self):
        for rec in self:
            rec.related_user_ids = rec.project_id.assigned_forensic_team_id.forensic_member_ids.mapped('member_ids')
    
    @api.onchange('sla_days','allocated_hours')
    def _onchange_sla_days(self):
        if self.sla_days < 0:
            raise ValidationError("SLA should be Positive.")

        if self.allocated_hours < 0 or self.allocated_hours > 24:
            raise ValidationError("Estimate should be 0-24 hours.")

    @api.constrains('planned_date_begin','date_deadline','project_id.date_start')
    def _check_planned_date(self):
        for rec in self:
            if rec.planned_date_begin and rec.date_deadline:
                if rec.planned_date_begin > rec.date_deadline:
                    raise ValidationError("The planned start date must be before the completion date.")
                
            if rec.is_sla == 'yes':
                if rec.planned_date_begin and rec.project_id.date_start:
                    if rec.planned_date_begin.date() < rec.project_id.date_start:
                        raise ValidationError("The start date must be after the investigation planned date.")
                
            if rec.is_sla == 'no':
                if rec.planned_date_begin and rec.project_id.date_start:
                    if rec.planned_date_begin.date() < rec.project_id.date_start:
                        raise ValidationError("The start date must be after the investigation planned date.")
                           

    @api.onchange('planned_date_begin', 'sla_days','is_sla')
    def _check_completion_date(self):
        if self.is_sla == 'yes' and self.sla_days and self.planned_date_begin:
            working_days = []
            days_line = self.env['resource.calendar'].search([('company_id', '=', self.company_id.id)],order='id desc', limit=1).mapped('attendance_ids')
            if not days_line:
                raise ValidationError("Please configure the working schedule.")

            for attendance in days_line:
                working_days.append(attendance.dayofweek)

            days = list(set(map(int, working_days)))
            planned_date = self.planned_date_begin

            count = 0
            while count < self.sla_days:
                day_of_week = planned_date.weekday()
                holiday = self.env['in2it.public.holidays'].search([('date_from','<=',planned_date),('date_to','>=',planned_date),('calendar_id.company_id','=',self.company_id.id)])

                if day_of_week in days and not holiday:
                    count += 1
                planned_date += relativedelta(days=1)

            self.date_deadline = planned_date - relativedelta(days=1)


    @api.model
    def _get_approval_action_domain(self):
        if self.env.user.has_group('base.group_system') or self.env.user.has_group('in2it_forensic_services.group_fcm_admin'):
            # Admin sees all (except approved)
            return [('approval_status', '!=', 'approved')]
        else:
            # Manager sees only assigned tasks
            return [
                ('approval_status', '!=', 'approved'),
                ('user_id', '=', self.env.uid)
            ]

    @api.model
    def action_open_approval_tasks(self):
        action = self.env.ref(
            'in2it_project_management.action_investigation_plan_approval'
        ).read()[0]

        action['domain'] = self._get_approval_action_domain()

        return action

    @api.model_create_multi
    def create(self, values_list):
        res_records = super().create(values_list)

        for vals, record in zip(values_list, res_records):
            project_id = vals.get('project_id')
            if project_id:
                stages = [self.env.ref('in2it_project_management.project_task_stage_draft'),
                          self.env.ref('in2it_project_management.project_task_stage_to_approve'),
                          self.env.ref('in2it_project_management.project_task_stage_approved')]

                for stage in stages:
                    stage.sudo().write({
                        'project_ids': [(4, project_id)]
                    })
        return res_records

    @api.onchange('stage')
    def onchange_stage(self):
        for rec in self:
            if rec.stage == 'closed':
                rec.actual_completion_date = fields.Date.today()

    @api.onchange('date_deadline', 'planned_date_begin')
    def _onchange_planned_dates(self):
        # Override base behavior to prevent resetting planned_date_begin
        pass
