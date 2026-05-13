from odoo import models, fields, api, _
from ...in2it_forensic_services.models.crm_lead_forensic import get_financial_year
from odoo.exceptions import ValidationError


class RecommendationCategory(models.Model):
    _name = "recommendation.category"
    _description = "Recommendation Category"

    name = fields.Char(string="Name")


class ProjectCategory(models.Model):
    _name = "project.category"
    _description = "Project Category"
    _rec_name = 'name'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", required=True, readonly=True, default=lambda self: _('New'), tracking=True)
    project_id = fields.Many2one('project.project',string="Project",ondelete='cascade', tracking=True)
    category_id = fields.Many2one('recommendation.category',string="Category", tracking=True)
    category_description = fields.Text(string="Description", tracking=True)
    for_efs = fields.Boolean(string="For EFS", tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress','In Progress'),
        ('completed', 'Completed'),
        ('closed','Closed')
    ], tracking=True, default="draft", compute='_compute_rec_status')

    case_id = fields.Many2one(related="project_id.case_id")
    assign_by = fields.Many2one('res.users', string="Assign By", tracking=True)
    assignment_date = fields.Date(string="Assignment Date")
    annexure_ids = fields.One2many(
        'forensic.document.line',
        compute='_compute_annexure_and_exhibit_ids',
        string="Annexures"
    )

    exhibits_ids = fields.One2many(
        'complaint.physical.item',
        compute='_compute_annexure_and_exhibit_ids',
        string="Exhibits"
    )

    is_lead_investigator = fields.Boolean(related="project_id.is_lead_investigator")
    ed_action_line_ids = fields.One2many('ed.action.line', 'recom_id', string="ED Action")
    govt_action_line_ids = fields.One2many('ed.action.line', 'gov_recom_id', string="GOV team Action(s)")
    memo_status = fields.Selection(related='project_id.o_memo_status')
    completed_actions_count = fields.Integer(string='Pending Actions', compute='_compute_actions_count')
    all_actions_count = fields.Integer(string='Completed Actions', compute='_compute_actions_count')
    directorate_id = fields.Many2one(
        'forensic.directorate',
        related='project_id.directorate_id',
        store=True
    )

    def _compute_rec_status(self):
        for rec in self:
            if rec.for_efs:
                action_lines = rec.govt_action_line_ids.filtered(lambda l: l.action == 'action')
            else:
                action_lines = rec.ed_action_line_ids.filtered(lambda l: l.action == 'action')

            if action_lines:
                if all(l.is_complete for l in action_lines):
                    rec.status = 'closed'

                elif all(l.status in ['completed', 'disputed'] for l in action_lines):
                    rec.status = 'completed'

                elif any(l.status in ['completed', 'disputed'] for l in action_lines):
                    rec.status = 'in_progress'

                else:
                    rec.status = 'draft'
            else:
                rec.status = 'draft'

    def _compute_actions_count(self):
        for rec in self:
            if rec.for_efs:
                rec.completed_actions_count = len(self.govt_action_line_ids.filtered(
                    lambda l: l.status not in ['pending']))
                rec.all_actions_count = len(self.govt_action_line_ids)

            else:
                rec.completed_actions_count = len(self.ed_action_line_ids.filtered(
                    lambda l: l.status not in ['pending'])
                )
                rec.all_actions_count = len(self.ed_action_line_ids)

    def _compute_annexure_and_exhibit_ids(self):
        for rec in self:
            if rec.project_id:
                rec.annexure_ids = rec.project_id.document_line_ids.filtered(
                    lambda l: l.is_annexure
                )

                rec.exhibits_ids = rec.project_id.physical_item_ids.filtered(
                    lambda l: l.is_exhibit
                )

    def write(self, vals):
        old_values = {}

        for rec in self:
            old_values[rec.id] = {
                'category': rec.category_id.name or '',
                'description': rec.category_description or '',
            }

        res = super().write(vals)

        for rec in self:
            if not rec.project_id:
                continue
            messages = []
            old = old_values.get(rec.id)

            # Category change
            if 'category_id' in vals:
                old_category = old['category']
                new_category = rec.category_id.name or ''
                if old_category != new_category:
                    messages.append(
                        f"Category: {old_category} → {new_category}"
                    )

            # Description change
            if 'category_description' in vals:
                old_description = old['description']
                new_description = rec.category_description or ''

                if old_description != new_description:
                    messages.append(
                        f"Description: "
                        f"{old_description or '-'} "
                        f" → {new_description or '-'}"
                    )

            # Post only if something changed
            if messages:
                rec.project_id.message_post(
                    body="<br/><br/>".join(messages)
                )

        return res
    
    def action_check_governence_member(self):
        for rec in self:
            unit_id = self.env.ref('in2it_forensic_services.department_proactive_and_gov_unit_3').id
            pfo_id = self.env.ref('in2it_project_management.')

            department_id = self.env['hr.department'].search([('id','=',unit_id.id)])
            employee = self.env['hr.employee'].search([('department_id','=',department_id.id)])


    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = f'/my/recommendations/{rec.id}'

    def action_preview_investigation_report(self):
        return self.env.ref('in2it_project_management.action_investigation_report').report_action(self.project_id)

    def action_overarching_memo(self):
        memo_id = self.env['overarching.memo'].search([('project_id', '=', self.project_id.id)], limit=1)
        return {
            'name': _("Overarching Memo"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'overarching.memo',
            'res_id': memo_id.id,
            'context': {
                'create': 0,
            }
        }

    def action_open_rec_lines(self):
        domain = []
        if self.for_efs:
            domain = [('gov_recom_id', '=', self.id)]
        else:
            domain = [('recom_id', '=', self.id)]

        list_view = self.env.ref('in2it_project_management.recom_action_list_view').id
        form_view = self.env.ref('in2it_project_management.recom_action_form_view').id
        return {
            'name': _("Recommendation Action(s)"),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'ed.action.line',
            'views': [(list_view, 'list'), (form_view, 'form')],
            'domain': domain,
            'context': {
                'for_efs': self.for_efs,
            }
        }

    def unlink(self):
        admin = self.env.user.has_group('base.group_system') \
                or self.env.user.has_group('in2it_forensic_services.group_fcm_admin')
        if not admin:
            raise ValidationError("Only Administrator can delete this record.")
        return super().unlink()
    

    @api.model_create_multi
    def create(self, vals_list):
        year = get_financial_year(self.env)
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                seq = self.env['ir.sequence'].next_by_code('project.category') or '0000'
                vals['name'] = f"REC/{year}/{seq}"
        return super().create(vals_list)
    

class EdActionLine(models.Model):
    _name = 'ed.action.line'
    _description = 'Executive Director Line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    recom_id = fields.Many2one('project.category', string="Recommendation")
    gov_recom_id = fields.Many2one('project.category', string="Gov Recommendation")
    user_id = fields.Many2one('res.users', string="Assigned To")
    action_date = fields.Date(string="Action Date", tracking=True)
    remark = fields.Text(string="Remark")
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments")
    action = fields.Selection([('action', 'Action'),('info','Information')], string="Action", tracking=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('disputed', 'Disputed'),
        ('completed', 'Completed')], string="Stage", default="pending", tracking=True)
    action_by = fields.Many2one('res.users', string="Action By", tracking=True)
    is_complete = fields.Boolean(string="Status", tracking=True)
    for_efs = fields.Boolean(string="For Efs")
    is_lead_investigator = fields.Boolean(compute='_compute_is_lead_investigator', string="Is Lead Investigator")
    is_close = fields.Boolean(string="Is Close")
    is_gov_user = fields.Boolean(string="Is Gov User", compute='_compute_is_gov_user')

    def _compute_is_gov_user(self):
        user = self.env.user
        for rec in self:
            if user.has_group('in2it_project_management.group_cms_governance')\
                or user.has_group('base.group_system'):
                rec.is_gov_user = True
            else:
                rec.is_gov_user = False

    def _compute_is_lead_investigator(self):
        user = self.env.user
        admin = self.env.user.has_group('base.group_system')\
                 or self.env.user.has_group('in2it_forensic_services.group_fcm_admin')

        for rec in self:
            recom_id = rec.recom_id or rec.gov_recom_id
            if recom_id and user in recom_id.project_id.assigned_forensic_team_id.project_investigator_ids or admin:
                rec.is_lead_investigator = True
            else:
                rec.is_lead_investigator = False

    def action_mark_as_done(self):
        for rec in self:
            rec.is_complete = True

    def action_submit_feedback(self):
        return {
            'name': _('Submit Feedback'),
            'type': 'ir.actions.act_window',
            'res_model': 'recom.submit.feedback.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_recom_action_id': self.id,
            }
        }

    def action_mark_done(self):
        self.is_close = True

    @api.depends('recom_id', 'gov_recom_id')
    def _compute_display_name(self):
        for record in self:
            if record.recom_id:
                record.display_name = record.recom_id.project_id.name
            else:
                record.display_name = record.gov_recom_id.project_id.name

    def unlink(self):
        admin = self.env.user.has_group('base.group_system') \
                or self.env.user.has_group('in2it_forensic_services.group_fcm_admin')
        if not admin:
            raise ValidationError("Only Administrator can delete this record.")
        return super().unlink()

