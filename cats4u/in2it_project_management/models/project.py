# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from datetime import datetime, time
import json



class InheritProject(models.Model):
    _inherit = 'project.project'

    case_limitation = """
                        <ol>
                            <li>
                                This report is based on the facts established from the documentation reviewed
                                and information obtained during the investigation and from the persons interviewed.
                                Should we receive any additional information after the date of issuing of this report,
                                our findings and recommendations may change.
                            </li>
                            <li>
                                Although our report may contain references to relevant laws and legislation,
                                we do not provide legal opinion on the compliance with such laws and our findings
                                in this report are not to be construed as providing legal advice.
                            </li>
                            <li>
                                We do not comment on the innocence or guilt of any person but merely report on the facts at our disposal.
                                It is the prerogative of a properly constituted legal forum to pronounce upon the guilt or innocence of an individual.
                            </li>
                            <li>
                                This report was prepared solely for the purpose of reporting our findings to the persons listed on the distribution list detailed above. It was prepared for possible use in legal proceedings and may contain confidential information that relates to CCT staff members, third parties and commercial activities ofthe CCT. Therefore, no part may be quoted, referred to, or disclosed in whole or in part, by any party without the consent of the CM.
                            </li>
                            <li>
                                Where we have conducted searches on public databases and since we do not control same, we can provide no undertaking as to the accuracy or correctness of the information obtained during such searches.
                            </li>
                            <li>
                                It should be noted that where applicable and/or appropriate,interviews/consultations with role players were conducted telephonically or via Microsoft Teams.
                            </li>
                            <li>
                                In conducting this investigation, only the relevant aspects of interviews/consultations conducted have been recorded herein and those parts not recorded should not be construed as not having been considered. Furthermore, it should be noted that all the aspects raised during this investigation were considered despite not making express reference thereto.
                            </li>
                        </ol>
                    """
    
    case_procedure_performed = """
                                <p>5.1. We performed, inter alia, the procedures listed below to achieve the objectives of the investigation.</p>
                                <p>5.2. <b>Interviews</b></p>
                                <ol style="padding-left: 25px;">
                                    <li>
                                        We interviewed and obtained information from various persons, including CCT employees and third parties.
                                    </li>
                                    <li>
                                        We recorded the interviews that we conducted and relied upon in this report with the consent of the interviewees.
                                    </li>
                                </ol>
    
                                <p>5.3. <b>Documents collected and reviewed</b></p>
                                <ol style="padding-left: 25px;">
                                    <li>
                                        We obtained and reviewed various documents, data extracts and/or electronic communications relevant to this investigation, which included, inter alia, the tender submissions of and in relation to Tender.
                                    </li>
                                </ol>
    
                                <p>5.4. <b>Background searches</b></p>
                                <ol style="padding-left: 25px;">
                                    <li>
                                        We performed background searches, using publicly available databases, in respect of individuals and/or entities identified during the investigation.
                                    </li>
                                    <li>
                                        The purpose of the background searches was to identify any information/evidence that may be of significance to the investigation, as well as highlight any possible conflicts of interest.
                                    </li>
                                </ol>
    
                                <p>5.5. <b>Digital evidence collected and reviewed</b></p>
                                <ol style="padding-left: 25px;">
                                    <li>
                                        This section should identify any desktop/laptop computers, network servers, mobile phones and other electronic storage devices, e.g., Hard Disk Drives (HDDs), Solid State Drives (SSDs), and USB Flash Drives that were identified for collection and analysis.
                                    </li>
                                    <li>
                                        The section must also include a brief explanation of the digital forensic methodologies that were followed to collect, process and analyse the collected electronic data.
                                    </li>
                                </ol>
                            """
    
    control_issues = """
                        <div style="margin-left:30px; text-indent:-28px; text-align: justify;">
                            9.1.
                            EFS identified control weaknesses that are relevant to the scope of this investigation and may have contributed to the identified irregularities.
                        </div>
    
                        <div style="margin-left:30px; text-indent:-28px; margin-top:6px; text-align: justify;">
                            9.2.
                            Any other control matters not directly related to the scope of this investigation will be addressed separately in the covering communication to management.
                        </div>
                    """
    

    user_id = fields.Many2one('res.users', string='Investigation Manager', default=lambda self: self.env.user, tracking=True)
    project_role_ids = fields.One2many('project.role', 'project_id', string='Project Roles')
    case_type_id = fields.Many2one('forensic.assignment.type', string="Case Type", tracking=True)
    case_id = fields.Many2one('crm.lead', string="Case", tracking=True)
    directorate_id = fields.Many2one('forensic.directorate', string="Directorate", related='case_id.directorate_id')
    department_id = fields.Many2one('forensic.department', string="Department", related='case_id.department_id')

    assignment_id = fields.Many2one('forensic.case.assignment', string="Case Assignment", tracking=True)
    assignment_type_id = fields.Many2one(related="assignment_id.assignment_type_id", string="Assignment Case Type")
    allegation_nature_id = fields.Many2one(related="assignment_id.allegation_nature_id")
    assignment_type = fields.Selection([('internal', 'Internal'), ('external', 'External')], default='internal',
                                       string="Case Handling Type", tracking=True)
    is_external_report_submitted = fields.Boolean("is external report submitted", default=False)
    is_create_task = fields.Boolean("Is Create Task")
    approval_status = fields.Selection([('draft', 'Draft'), ('pending', 'Pending'), ('approved', 'Approved')],
                                       default="draft", string="Approval Status")

    case_background = fields.Html(
        string="Case Background",
        compute="_compute_case_background",
        store=True
    )

    @api.depends('case_id')
    def _compute_case_background(self):
        for rec in self:
            if rec.case_id:
                rec.case_background = f"""
                    The matter originated from 
                    {rec.case_id.allegation_source_id.name or ''}, 
                    {rec.case_id.allegation_nature_id.name or ''}, 
                    {rec.case_id.partner_id.name or ''}, 
                    and these were the witnesses and suspects involved 
                    {', '.join(rec.witness_ids.mapped('name'))}, 
                    {', '.join(rec.suspect_ids.mapped('name'))} 
                    and relates to 
                    {rec.department_id.name or ''}, 
                    {rec.directorate_id.name or ''}.
                """
            else:
                rec.case_background = ""
    
    operational_risks = fields.Html(string="Operational Risks")
    chief_id = fields.Many2one('res.users', string='Chief', help='This is used to send reports',
                               default=lambda self: self.env['res.users'].search([('groups_id', 'in', self.env.ref(
                                   'in2it_forensic_services.group_fcm_case_chief_access').id)], limit=1))

    priority = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
                                string="Assignment Priority", tracking=True, default='low')
    suspect_ids = fields.One2many(
        comodel_name='forensic.case.suspects',
        inverse_name='project_id',
        string="Suspects",
        help='List of suspects linked to this case.'
    )

    attachment = fields.Char("Documents", tracking=True)

    physical_item_ids = fields.One2many(
        comodel_name='complaint.physical.item',
        inverse_name='project_id',
        string="Physical Items Received"
    )

    record_access = fields.Selection(
        [('read', 'Read'), ('write', 'Write')],
        string="Record Access",
        compute="_compute_record_access"
    )
    scheduled_meeting_count = fields.Integer(string="Meeting Schedule Count", default="0", compute="_compute_schedule_meeting_count")
    recom_project_ids = fields.One2many('project.category', 'project_id', string="Recommendations")
    findings = fields.Html(string="Findings")

    manager_domain = fields.Char(string="Manager Domain IDS", compute='_get_default_manager_ids')

    investigation_objective = fields.Html(string="Case Objective")
    investigation_scope = fields.Html(string="Case Scope")
    regulatory_operational_env = fields.Html(string="Regulatory and Operational Environment")
    is_lead_investigator = fields.Boolean(string="Is Lead Investigator", compute="_check_lead_investigator")

    document_line_ids = fields.One2many(comodel_name='forensic.document.line', inverse_name="project_id",
                                        string="Document Line")

    background_count = fields.Integer(string="Background Check Count", compute="_action_compute_background_check_count")
    background_completed_count = fields.Integer(string="Background Check Complete Count", compute="_action_compute_background_check_count")
    limitations = fields.Html(string="Limitations",default=case_limitation)
    conclusions = fields.Html(string="Conclusions")
    control_issues = fields.Html(string="Control Issues",default=control_issues)
    procedure_performed = fields.Html(string="Procedure Performed", default=case_procedure_performed)
    witness_ids = fields.One2many(
        comodel_name='forensic.case.witness',
        inverse_name='project_id',
        string="Witnesses"
    )
    show_report = fields.Boolean(
        string="Is Report",
        compute="_action_show_report"
    )
    partner_id = fields.Many2one('res.partner', string='Customer', auto_join=True, tracking=True, domain="['|', ('company_id', '=?', company_id), ('company_id', '=', False)]", related="case_id.partner_id")
    can_edit_manager = fields.Boolean(default=False, string="Can edit manager", compute="_compute_can_edit_manager")

    assigned_pfo_id = fields.Many2one('res.users',string="Assigned PFO")

    case_type = fields.Selection([('pre', 'PRE'),('for', 'FOR'),('lsa', 'LSA'),('dfo', 'DFO'),('eth', 'ETH')], default=False, string="Assigned Case Type", compute="_compute_case_type_name", store=True)
    peer_review_count = fields.Integer(compute="compute_peer_review_count")
    is_project_stage = fields.Selection([('under_investigation', 'Under Investigation')], default=False, string="Project Stage", compute="_compute_project_stage", store=False)
    distribution_line_ids = fields.One2many('distribution.line','project_id',string="Distribution List")
    distribution_count = fields.Integer(compute='_compute_distribution_count')
    pfo_domain = fields.Char(string="PFO Domain", compute="_get_default_pfo_ids")
    investigation_directorates_ids = fields.One2many('inv.dir.dept', 'investigation_id', string="Investigation Directorates")
    final_report_upload_date = fields.Date(string="Final Report Upload Date", help="External case: PFO Final Report Upload Date")
    report_signoff_date = fields.Date(string="Report review signoff Date", help="Inv Report Peer Review Manager signoff Date")

    def _get_default_pfo_ids(self):
        for rec in self:
            job = self.env.ref('in2it_forensic_services.principle_of_forensic_officer')
            pfo_ids = self.env['hr.employee'].search([('job_id', '=', job.id)])
            rec.pfo_domain = json.dumps([('employee_id', 'in', pfo_ids.ids)])

    tor_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved')], string="TOR Status", compute='_compute_tor_status')

    report_review_status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed')], default="pending", string="Report Review Status", compute='_compute_report_review_status')

    o_memo_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved')], default="pending", string="Overarching Memo Status",
        compute='_compute_overarching_memo_status')

    def _compute_overarching_memo_status(self):
        for rec in self:
            o_memo_id = self.env['overarching.memo'].search([('project_id', '=', rec.id)], limit=1)
            if o_memo_id and o_memo_id.status == 'approved':
                rec.o_memo_status = 'approved'
            else:
                rec.o_memo_status = 'pending'

    def _compute_report_review_status(self):
        for rec in self:
            report_review_id = self.env['forensic.peer.review'].search([('project_id', '=', rec.id)], limit=1)
            if report_review_id and report_review_id.state == 'complete':
                rec.report_review_status = 'completed'
            else:
                rec.report_review_status = 'pending'

    def _compute_project_stage(self):
        for rec in self:
            rec.is_project_stage = False
            if rec.stage_id.id == self.env.ref('project.project_project_stage_1').id:
                rec.is_project_stage = 'under_investigation'

    def _compute_tor_status(self):
        for rec in self:
            tor = self.env['investigation.vendor.tor'].search([('project_id', '=', rec.id)], limit=1)
            if tor and tor.status == 'approved':
                rec.tor_status = 'approved'
            else:
                rec.tor_status = 'pending'


    def _compute_distribution_count(self):
        for rec in self:
            rec.distribution_count = len(rec.distribution_line_ids)

    @api.depends('assignment_type_id')
    def _compute_case_type_name(self):
        for rec in self:
            rec.case_type = False
            if rec.assignment_type_id == self.env.ref('in2it_forensic_services.assignment_type_preliminary'):
                rec.case_type = 'pre'
            elif rec.assignment_type_id == self.env.ref('in2it_forensic_services.assignment_type_forensic'):
                rec.case_type = 'for'
            elif rec.assignment_type_id == self.env.ref('in2it_forensic_services.assignment_type_lsa'):
                rec.case_type = 'lsa'
            elif rec.assignment_type_id == self.env.ref('in2it_forensic_services.assignment_type_dfo'):
                rec.case_type = 'dfo'
            elif rec.assignment_type_id == self.env.ref('in2it_forensic_services.assignment_type_eth'):
                rec.case_type = 'eth'

    def _compute_can_edit_manager(self):
        """If logged-in user is the part of admin group (system admin, FCM admin or governance team) then can edit the
        investigation manager field
        """
        user = self.env.user
        self.can_edit_manager = False
        can_edit = (
                user.has_group('base.group_system') or
                user.has_group('in2it_forensic_services.group_fcm_admin') or
                user.has_group('in2it_project_management.group_cms_governance')
        )
        for rec in self:
            rec.can_edit_manager = can_edit


    assigned_forensic_team_count = fields.Integer(string="Forensic Team Count", compute="action_assigned_forensic_team_count", default=0)
    def action_assigned_forensic_team_count(self):
        for rec in self:
            rec.assigned_forensic_team_count = self.env['assigned.forensic.team'].search_count([('project_id','=',self.id)])

    assigned_forensic_team_id = fields.Many2one('assigned.forensic.team', string="Assigned Forensic team")
    partner_line_ids = fields.One2many('investigation.vendor.line', 'project_id',string="Vendor", tracking=True)

    @api.depends('stage_id')
    def _action_show_report(self):
        stage_planning_ref = self.env.ref(
            'project.project_project_stage_0',
            raise_if_not_found=False)

        for rec in self:
            rec.show_report = True
            if rec.stage_id and (
                (stage_planning_ref and rec.stage_id.id == stage_planning_ref.id)):
                rec.show_report = False


     # Working for INvestigation Team Smart Button
    def _compute_record_access(self):
        user = self.env.user
        for rec in self:
            is_admin = self.env.user.has_group('base.group_system')
            rec.record_access = 'write'  # default
            assigned_team = self.env['assigned.forensic.team'].search([('project_id','=',rec.id)], limit=1)
            if assigned_team:
                if user in assigned_team.project_investigator_ids or is_admin: # If user is the part of LI & forensic member both
                    rec.record_access = 'write'

                elif user in assigned_team.forensic_member_ids.member_ids: # If user is the member only
                    rec.record_access = 'read'


    def write(self, vals):
        res = super().write(vals)
 
        template = False
        if 'user_id' in vals:
            template = self.env.ref(
                'in2it_project_management.mail_template_case_assigned_investigation',
                raise_if_not_found=False
            )
 
        # Get model once
        res_model_id = self.env['ir.model'].search(
            [('model', '=', self._name)], limit=1
        )
 
        for rec in self:
 
            # ------------------ PM Assignment ------------------
            if 'user_id' in vals and rec.user_id and rec.user_id.email:
                if template:
                    template.send_mail(
                        rec.id,
                        force_send=True,
                        email_values={
                            'email_to': rec.user_id.email,
                        }
                    )
 
                    if res_model_id:
                        self.env['system.notification'].create({
                            'message': f"Case {rec.name} assigned to you as Investigation Manager.",
                            'user_id': rec.user_id.id,
                            "res_model_id": res_model_id.id,
                            "res_id": rec.id
                        })
 
            # ------------------ PFO Assignment ------------------
            if 'assigned_pfo_id' in vals and vals.get('assigned_pfo_id'):
                if rec.assigned_pfo_id:
 
                    if res_model_id:
                        self.env['system.notification'].create({
                            'message': f"Case {rec.name} assigned to you as Principal Forensic Officer.",
                            'user_id': rec.assigned_pfo_id.id,
                            "res_model_id": res_model_id.id,
                            "res_id": rec.id
                        })
 
        return res
 

    @api.model_create_multi
    def create(self, vals_list):
        # create record
        record =  super().create(vals_list)

        # mail template
        template = self.env.ref(
            'in2it_project_management.mail_template_case_assigned_investigation',
            raise_if_not_found=False
        )

        if template:
            for rec in record:
                if rec.user_id and rec.user_id.email:
                    # Send mail to notify Manager
                    template.send_mail(
                        rec.id,
                        force_send=True,
                        email_values={
                            'email_to': rec.user_id.email
                        }
                    )
        return record

    def _get_default_manager_ids(self):
        for rec in self:
            manager_ids = self.env['hr.department'].search([('manager_id', '!=', False),('is_forensic_dep', '=', True)]).mapped('manager_id').ids
            rec.manager_domain = json.dumps([('employee_id', 'in', manager_ids)])

    def action_assign_standard_task(self):
        self.ensure_one()
        return {
            'name': 'Assign Standard Tasks',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.standard.task.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'create': False,
                'default_project_id': self.id,
            }
        }

    def action_request_investigation_plan(self):
        self.ensure_one()
        if not self.assigned_forensic_team_id.project_investigator_ids:
            raise ValidationError(_("No Lead Investigator Assigned."))
        # Get project stages ordered by sequence
        stages = self.type_ids.sorted('sequence')
        if not stages:
            raise UserError(_("No stages configured for this project."))

        tasks_without_deadline = self.task_ids.filtered(
            lambda t: not t.planned_date_begin or not t.date_deadline
        )

        if tasks_without_deadline:
            raise ValidationError(
                "These tasks are missing Start/End Date:\n%s" %
                "\n".join(tasks_without_deadline.mapped('name'))
            )

        for task in self.task_ids:
            # Skip if no stage
            if not task.stage_id:
                continue
            # Find current stage index
            try:
                current_index = stages.ids.index(task.stage_id.id)
            except ValueError:
                continue  # stage not part of project stages

            # If already last stage → skip
            if current_index + 1 >= len(stages):
                continue
            next_stage = stages[current_index + 1]
            task.stage_id = next_stage.id

        self.write({'approval_status': 'pending'})
        if self.user_id:
            user = self.user_id
            template = self.env.ref(
                'in2it_project_management.mail_template_investigation_plan_submitted',
                raise_if_not_found=False
            )
            if template:
                template.with_context(case_id=self.case_id.name).send_mail(
                    self.id,
                    force_send=True,
                    email_values={'email_to': user.email}
                )
        # System Notification
        model = self._name
        if model:
            res_model_id = self.env['ir.model'].search([('model','=',model)])
        if res_model_id:
            self.env['system.notification'].create({
                'message':f"Plan Awaiting Review – Investigation Plan for Case {self.name} submitted by {self.assigned_forensic_team_id.project_investigator_ids[0].name}.",
                'user_id':self.user_id.id,
                "res_model_id":res_model_id.id or False,
                "res_id":self.id
            })

    scheduled_meeting_count = fields.Integer(string="Meeting Schedule Count", default="0", compute="_compute_schedule_meeting_count")
    evidence_count = fields.Integer(string="Evidence Count", default="0", compute="_compute_digital_evidence_count")
    overarching_memo_count = fields.Integer(string="Overarching Memo Count", default="0", compute="_compute_overarching_memo_count")
    complete_evidence_count = fields.Integer(string="Complete Evidence Count", default="0", compute="_compute_digital_evidence_count")
    recom_project_ids = fields.One2many('project.category','project_id',string="Recommendations")     
    findings = fields.Html(string="Findings")

    
    
    outsource_count = fields.Integer(string="Outsource Count", default="0", compute="_compute_outsource_count")

    def _compute_outsource_count(self):
        for rec in self:
            outsource_count = self.partner_line_ids.search_count([('project_id','=',self.id)])
            rec.outsource_count = outsource_count

    outsource_status = fields.Selection([
        ('new', 'New'), 
        ('pending', 'Pending'),
        ('accept', 'Accept'),
        ('reject', 'Reject')], default='new', compute='_action_get_outsource_status')
    
    @api.depends('assignment_type')
    def _action_get_outsource_status(self):
        for rec in self:
            rec.outsource_status = False
            if rec.assignment_type == 'external':
                rec.outsource_status = 'new'
                if rec.partner_line_ids:
                    all_inactive = all(r.status in ['reject', 'expire'] for r in rec.partner_line_ids)
                    confirm_vendor = any(r.status in ['accept'] for r in rec.partner_line_ids)
                    pending_vendor = any(r.status in ['pending'] for r in rec.partner_line_ids)
                    if  all_inactive:
                        rec.outsource_status = 'reject'
                    if confirm_vendor:
                        rec.outsource_status = 'accept'
                    if pending_vendor:
                        rec.outsource_status = 'pending'

    def action_open_outsources(self):
        return {
            'name': _('Outsources'),
            'type': 'ir.actions.act_window',
            'res_model': 'investigation.vendor.line',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'create': False,
                'edit': False,
                'delete': True,
            },
        }
        
    def _move_project_stage(self):
        """Move project to next stage based on sequence"""
        for rec in self:
            if not rec.stage_id:
                continue

            next_stage = self.env['project.project.stage'].search([('sequence', '>', rec.stage_id.sequence)],
                                                                  order='sequence asc', limit=1)
            if next_stage:
                rec.stage_id = next_stage.id


    def action_approve_investigation_plan(self):
        self.ensure_one()
        if not self.task_ids:
            raise ValidationError(_("No investigation plan created for this project."))
        self.task_ids.action_approve_task()
        return True


    def action_preview_investigation_plan(self):
        self.ensure_one()

        # Fetch the specific Gantt view record
        gantt_view = self.env.ref(
            'project_enterprise.project_task_dependency_view_gantt',
            raise_if_not_found=False
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Investigation Plan',
            'res_model': 'project.task',
            'view_mode': 'gantt,kanban,list,form',
            # The first tuple in 'views' will be the default view opened
            'views': [(gantt_view.id if gantt_view else False, 'gantt'), (False, 'kanban'), (False, 'list'), (False, 'form')],
            'domain': [
                ('project_id', '=', self.id),
                ('display_in_project', '=', True),
            ],
            'context': {
                'default_project_id': self.id,
                'active_model': 'project.project',
                'create':False
            },
            'target': 'current',
        }


    @api.constrains('user_id', 'assigned_forensic_team_id')
    def _check_manager_investigators(self):
        for rec in self:
            forensic_mem_ids = rec.assigned_forensic_team_id.forensic_member_ids.mapped('member_ids').ids
            if rec.user_id and forensic_mem_ids:
                if rec.user_id.id in forensic_mem_ids:
                    raise ValidationError("Investigation manager cannot be a part of Investigation Team.")
                
    
    @api.constrains('date_start')
    def _check_investigation_date(self):
        for rec in self:
            if rec.date_start and rec.create_date:
                if rec.date_start < rec.create_date.date():
                    raise ValidationError("Start Date cannot be before Authorization Date.")


    @api.depends('assigned_forensic_team_id', 'assigned_pfo_id', 'assignment_type')
    def _check_lead_investigator(self):
        is_admin = self.env.user.has_group('base.group_system')
        for rec in self:
            rec.is_lead_investigator = (
                is_admin or
                (rec.assignment_type == 'internal' and
                self.env.user in rec.assigned_forensic_team_id.project_investigator_ids) or
                (rec.assignment_type == 'external' and
                rec.assigned_pfo_id and
                self.env.user == rec.assigned_pfo_id)
            )


    def _compute_schedule_meeting_count(self):
        today_datetime = datetime.combine(fields.date.today(), time.min)
        today_date = fields.date.today()
        for rec in self:
            schedule_meeting_count = self.env['calendar.event'].search_count([('project_id','=',rec.id),'|',('start','>=',today_datetime),('start_date','>=',today_date)])
            rec.scheduled_meeting_count = schedule_meeting_count

    def action_scheduled_meeting(self):
        self.ensure_one()
        today_datetime = datetime.combine(fields.date.today(), time.min)
        today_date = fields.date.today()
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        action['context'] = {
            'default_project_id': self.id,
            'default_case_id': self.case_id.id,
            'today_datetime': today_datetime,
            'today_date': today_date,
            'search_default_futuremeetings': 1,
        }
        action['domain'] = [('project_id', '=', self.id)]
        action['target'] = 'current'
        return action

    def _action_compute_background_check_count(self):
        self.background_count = self.env['background.check.details'].search_count([('project_id', '=', self.id)])
        self.background_completed_count = self.env['background.check.details'].search_count([
            ('project_id', '=', self.id),
            ('status', 'in', ['completed','cancelled']),
        ])

    def action_open_background_check_details(self):
        return {
            'name': _("Background Check"),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'background.check.details',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
            }
        }
    
    
    def action_open_tor(self):
        tor = self.env['investigation.vendor.tor'].search(
                [('project_id', '=', self.id)], limit=1
            )

        return {
            'name': _("TOR"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'investigation.vendor.tor',
            'res_id': tor.id if tor else False,
            'context': {
                'default_project_id': self.id,
                'default_case_id': self.case_id.id,
            }
        }
    
    def _compute_digital_evidence_count(self):
        for rec in self:
            evidence_count = self.env['digital.evidence'].search_count([('project_id','=',rec.id)])
            complete_evidence_count = self.env['digital.evidence'].search_count([
                ('project_id','=',rec.id),
                ('status','=','approved')
            ])
            rec.evidence_count = evidence_count
            rec.complete_evidence_count = complete_evidence_count

    def _compute_overarching_memo_count(self):
        for rec in self:
            memo_count = self.env['overarching.memo'].search_count([('project_id','=',rec.id)])
            rec.overarching_memo_count = memo_count

    def action_digital_evidence(self):
        return {
            'name' : _("Digital Evidence"),
            'type' : 'ir.actions.act_window',
            'view_mode' : 'list,form',
            'res_model' : 'digital.evidence',
            'domain' : [('project_id','=',self.id)],
        }

    def action_overarching_memo(self):
        memo_id = self.env['overarching.memo'].search(
                    [('project_id', '=', self.id)], limit=1
                )
        
        return {
            'name' : _("Overarching Memo"),
            'type' : 'ir.actions.act_window',
            'view_mode' : 'form',
            'res_model' : 'overarching.memo',
            'res_id': memo_id.id,
            'context': {
                'create': 0,
            }           
        }

    def action_request_digital_access_by_lead_investigator(self):
        self.ensure_one()
        suspect = self.env['forensic.case.suspects'].search([('project_id','=', self.id)])
        return {
            'name': 'Request for Digital Access',
            'type': 'ir.actions.act_window',
            'res_model': 'request.digital.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'suspects': suspect.ids if suspect else [],
            }
        }
    
    def action_generate_overarching_memo(self):
        self.ensure_one()
        review_id = self.env['forensic.peer.review'].search([('project_id','=',self.id)], limit=1)
        return {
            'name': 'Overarching Memo',
            'type': 'ir.actions.act_window',
            'res_model': 'overarching.memo.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_case_type': self.case_type,
                'default_directorate_id': self.directorate_id.id,
                'default_allegation_nature_id': self.allegation_nature_id.id,
                'default_lead_investigator_ids': self.assigned_forensic_team_id.project_investigator_ids.ids
                                                    if self.assignment_type == 'internal'
                                                    else [self.assigned_pfo_id.id] if self.assigned_pfo_id else [],
                'default_investigator_id': self.user_id.id,
                'default_approval_date': review_id.sign_off_date,
            }
        }

    def action_open_assign_pm_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Investigation Manager',
            'res_model': 'assign.project.manager.wizard',
            'view_mode': 'form',
            'target': 'new'
        }

    def action_generate_investigation_report(self):
        self.ensure_one()
        if not self.department_id:
            raise ValidationError("Department is required.")
        if not self.date_start or not self.date:
            raise ValidationError("Planned Date is required.")
        if not self.partner_id:
            raise ValidationError("Complainant is required.")
        if not self.directorate_id:
            raise ValidationError("Directorate is required.")
        if not self.assigned_forensic_team_id.forensic_member_ids:
            raise ValidationError("Forensic Member is required.")
        if not self.witness_ids:
            raise ValidationError("Case Witness is required.")
        if not self.suspect_ids:
            raise ValidationError("Suspects is required.")
        if not self.physical_item_ids:
            raise ValidationError("Evidence is required.")
        if not self.document_line_ids:
            raise ValidationError("Documentation is required.")
        if not self.project_role_ids:
            raise ValidationError("Roles & Abbreviations is required.")
        if not self.investigation_objective:
            raise ValidationError("Investigation objective is required.")
        if not self.investigation_scope:
            raise ValidationError("Investigation scope is required.")
        if not self.case_background:
            raise ValidationError("Case background Scope is required.")
        if not self.operational_risks:
            raise ValidationError("Operational risk Scope is required.")
        if not self.regulatory_operational_env:
            raise ValidationError("Regulatory operation field is required.")
        if not self.procedure_performed:
            raise ValidationError("Procedure perform is required.")
        if not self.limitations:
            raise ValidationError("Limitations is required.")
        if not self.control_issues:
            raise ValidationError("Control issues is required.")
        if not self.conclusions:
            raise ValidationError("Conclusions is required.")
        if not self.recom_project_ids:
            raise ValidationError("Recommendations is required.")

        if not self.distribution_line_ids:
            raise ValidationError("Please create distribution list before proceeding.")

        # validation for atleast one ED in distribution list
        ed_users = self.distribution_line_ids.mapped('user_id').filtered(
            lambda u: u.position == 'ed'
        )
        if not ed_users:
            raise ValidationError("At least one ED must be in the distribution list.")

        # call report
        return self.env.ref(
            'in2it_project_management.action_investigation_report'
        ).report_action(self)


    def action_open_distribution_lines(self):
        self.ensure_one()
        return {
            'name': 'Distribution List',
            'type': 'ir.actions.act_window',
            'res_model': 'distribution.line',
            'view_mode': 'list',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'create': self.is_lead_investigator
            }
        }

    def generate_preliminary_assessment_report(self):
        """Generate Preliminary assessment report"""
        self.ensure_one()
        return self.env.ref('in2it_project_management.action_pre_investigation_report').report_action(self)

    # Use To Opening Wizard Forensic Team
    def action_open_forensic_team_wiazrd(self):
        for rec in self:
            is_admin = self.env.user.has_group('base.group_system')
            if not (is_admin or rec.user_id.id == self.env.user.id):
                raise ValidationError("Only Admin and Investigation manager can create the team")
            assigned_record = self.env['assigned.forensic.team'].search([('project_id','=',self.id)],limit=1)
            if assigned_record:
                raise ValidationError("You have already assigned the team")

            return {
                'name': 'Investigation Team Members',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'forensic.team.wizard',
                'target':'new',
                'context': {
                    'default_project_id': self.id,
                }
            }
            
    # To opening smartbutton model forensic team
    def action_open_assigned_forensic_team(self):
        forensic_team = self.env['assigned.forensic.team'].search(
                    [('project_id', '=', self.id)], limit=1
                )

        return {
            'name': _("Assigned Investigation Team"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'assigned.forensic.team',
            'res_id': forensic_team.id,
            'context': {
                'create': 0,
            }

        }

    def compute_peer_review_count(self):
        ReviewLine = self.env['forensic.peer.review.line']
        for rec in self:
            data = ReviewLine.read_group(
                [('review_id.project_id', '=', rec.id)],
                ['user_id'],
                ['user_id']
            )
            rec.peer_review_count = len(data)

    def action_create_peer_review(self):
        self.ensure_one()
        if self.background_count < 1:
            raise UserError("At least one background check must be recorded in the system.")
        if not self.distribution_count:
            raise UserError("Please create the distribution list before starting the peer review.")
        team = self.assigned_forensic_team_id
        # Get forensic hierarchy
        members = team.forensic_member_ids.sorted(
            key=lambda m: m.job_id.sequence or 0,
            reverse=True
        )
        investigators = team.project_investigator_ids

        # Find highest investigator index
        highest_index = -1

        for i, member in enumerate(members):
            if any(user in investigators for user in member.member_ids):
                highest_index = max(highest_index, i)

        if highest_index == -1:
            raise UserError("Lead Investigators not found in investigation team.")

        # Create review
        review = self.env['forensic.peer.review'].create({
            'project_id': self.id,
            'state': 'pending'
        })
        # move project next stage i.e.Under Review
        self._move_project_stage()

        review_line_obj=False
        #  Determine next level
        next_index = highest_index + 1

        # CASE 1: Next forensic hierarchy exists
        if next_index < len(members):
            next_members = members[next_index]
            for user in next_members.member_ids:
                review_line_obj = self.env['forensic.peer.review.line'].create({
                    'review_id': review.id,
                    'user_id': user.id,
                    'action': 'pending',
                    'previous_reviewer_id': self.env.user.id
                })
                # System Notification
                res_model_id = self.env['ir.model'].search([('model', '=', 'forensic.peer.review')])
                if res_model_id and review_line_obj:
                    self.env['system.notification'].create({
                        'message': f"Report Awaiting Review – Investigation Report for {self.name} submitted.",
                        'user_id': review_line_obj.user_id.id,
                        "res_model_id": res_model_id.id or False,
                        "res_id": review.id
                    })

        else:
            # CASE 2: No higher forensic level -> go to Manager
            if self.user_id:
                review_line_obj = self.env['forensic.peer.review.line'].create({
                    'review_id': review.id,
                    'user_id': self.user_id.id,
                    'action': 'pending',
                    'previous_reviewer_id': self.env.user.id
                })

            # edge case: if no manager → go directly to chief
            elif self.chief_id:
                review_line_obj = self.env['forensic.peer.review.line'].create({
                    'review_id': review.id,
                    'user_id': self.chief_id.id,
                    'action': 'pending',
                    'previous_reviewer_id': self.env.user.id
                })
            else:
                raise UserError("No higher authority (Manager/Chief) found.")
            
            # System Notification
            res_model_id = self.env['ir.model'].search([('model','=','forensic.peer.review')])
            if res_model_id and review_line_obj:
                self.env['system.notification'].create({
                    'message':f"Report Awaiting Review – Investigation Report for {self.name} submitted.",
                    'user_id': review_line_obj.user_id.id,
                    "res_model_id":res_model_id.id or False,
                    "res_id": review.id
                })

        return review

    def action_open_peer_reviews(self):
        self.ensure_one()
        review_id = self.env['forensic.peer.review'].search(
                    [('project_id', '=', self.id)], limit=1
                )
        
        return {
            'name': 'Report Reviews',
            'type': 'ir.actions.act_window',
            'res_model': 'forensic.peer.review',
            'view_mode': 'form',
            'res_id': review_id.id,
            'context': {
                'default_project_id': self.id,
                'create':0
            }
        }

    def action_assign_vendor_wizard(self):
        if not self.user_id:
            raise ValidationError("Investigation Manager is required.")
        if not self.assigned_pfo_id:
            raise ValidationError("Principle Forensic Officer is required.")
        
        
        return {
            'name' : _("Add Vendor"),
            'view_mode' : 'form',
            'type' : 'ir.actions.act_window',
            'target' : 'new',
            'res_model' : 'assign.vendor.wizard',
            'context' : {
                'default_project_id' : self.id,
                'new_vendor' : True,
                'rejected_partner_domain' : [],
            }
        }


    def action_add_another_vendor(self):
        for rec in self:
            all_inactive = all(r.status in ['reject', 'expire'] for r in rec.partner_line_ids)
            rejected_partner_ids = self.env['investigation.vendor.line'].search([
                ('project_id', '=', rec.id),
                ('status', '=', 'reject')
            ]).mapped('partner_id').ids
            
            if all_inactive:
                return {
                    'name' : _("Add Another Outsource"),
                    'view_mode' : 'form',
                    'type' : 'ir.actions.act_window',
                    'target' : 'new',
                    'res_model' : 'assign.vendor.wizard',
                    'context' : {
                        'default_project_id' : self.id,
                        'another_vendor' : True,
                        'rejected_partner_domain':rejected_partner_ids
                    }
                }    

    def action_add_vendor_attachment(self):
        return {
            'name' : _('Add Report Attachment'),
            'type': 'ir.actions.act_window',
            'res_model': 'outsource.review.docs',
            'view_mode': 'form',
            'target': 'new',
        }    


    def _compute_access_url(self):
        super(InheritProject, self)._compute_access_url()
        for project in self:
            project.access_url = f'/ed/projects/{project.id}'