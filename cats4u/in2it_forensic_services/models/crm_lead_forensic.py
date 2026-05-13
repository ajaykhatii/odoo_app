# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################
import datetime
from email.policy import default

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.modules.registry import Registry
from datetime import date
import logging
import re
import phonenumbers

_logger = logging.getLogger(__name__)


# Helper Functions
def get_financial_year(env, company_id=None):
    """
    Return financial year in 'YY-YY' format based on company settings.
    Example: '25-26'
    """
    # Get company (current user’s company if not passed)
    company = env['res.company'].browse(company_id) if company_id else env.company

    # Ensure FY dates are configured
    if not company.fy_start_date or not company.fy_end_date:
        raise ValidationError("Financial Year dates are not configured in the Company settings.")

    fy_start_year = company.fy_start_date.year
    fy_end_year = company.fy_end_date.year

    return f"{fy_start_year % 100:02d}-{fy_end_year % 100:02d}"



EMAIL_REGEX = re.compile(
    r"(^[-!#$%&'*+/0-9=?A-Z^_`a-z{|}~]+"
    r"(\.[-!#$%&'*+/0-9=?A-Z^_`a-z{|}~]+)*"
    r"@([A-Za-z0-9]([-A-Za-z0-9]*[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,}$)"
)

def validate_email(email):
    """Validate email format using regex.
    Raise ValidationError if invalid."""
    if email and not EMAIL_REGEX.match(email):
        raise ValidationError(f"Invalid email format: {email}")
    return True


def validate_phone(phone, country_code=None):
    """
    Validates a phone number using the phonenumbers library.

    RULES:
    - If no country_code is passed → default = South Africa (SA) = 'ZA'
    - Phone number may include +27 or may be written without +27
    - If number is valid in ZA phone rules → accept
    - eg. valid - 0821234567, +27821234567
    """
    if not phone:
        return True  # no validation for empty strings

    # Default to SA = ZA
    region = (country_code or "ZA").upper()

    try:
        # Try parsing the number using the region (ZA if None provided)
        parsed = phonenumbers.parse(phone, region)

        # Check if the phone number is valid for that region
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError(f"Invalid phone number: {phone}")

        return True

    except phonenumbers.NumberParseException:
        raise ValidationError(f"Invalid contact number format: {phone}")

class CrmLeadForensic(models.Model):
    """Extend CRM Lead for Forensic Case Management"""
    _inherit = 'crm.lead'
    _description = 'Case Management'

    # ===== FORENSIC CASE IDENTIFICATION =====

    # no need to create a common sequence. It will update automatically based on the financial year change in the configuration settings
    internal_coms_ref = fields.Char(
        string='Internal Coms Reference ',
        tracking=True,
        help="Auto-generated unique internal complain reference"
    )

    offence_date_from = fields.Datetime(
        string="Alleged Offence Date",
        tracking=True
    )

    offence_date_to = fields.Datetime(
        string="Alleged Offence To Date",
        tracking=True
    )

    allegation_nature_id = fields.Many2one('forensic.allegation.nature', string="Nature of Allegation", ondelete='restrict', tracking=True)

    assignment_type_ids = fields.Many2many('forensic.assignment.type',
                                       string="Assignment Type",
                                       ondelete='restrict',
                                       tracking=True)

    case_assignment_count = fields.Integer(
        string="Case Assignments Count",
        compute="_compute_case_assignment_count"
    )
    case_classification_count = fields.Integer(
        string="Case Classification Count",
        compute="_compute_case_assignment_count"
    )

    create_investigation_count = fields.Integer(
        string="Create Investigation Count",
        compute="_compute_case_assignment_count"
    )

    case_assignment_ids = fields.One2many(
        'forensic.case.assignment',
        'parent_case_id',
        string="Case Assignments"
    )

    com_stage_id = fields.Many2one('forensic.assignment.stage',
                                   string='COM Stage', domain=[('is_common_stage', '=', True)], tracking=True,
                                   default=lambda self: self.env['forensic.assignment.stage'].search(
                                       [('is_common_stage', '=', True)], limit=1,
                                       order="sequence asc, id asc"))

    is_stage_case_intake = fields.Boolean(compute="_compute_stage_flags", store=False)
    is_stage_under_review = fields.Boolean(compute="_compute_stage_flags", store=False)
    is_stage_reviewed = fields.Boolean(related='com_stage_id.is_under_review', store=True)
    review_officer =  fields.Many2one("res.users", string="Review Officer")
    review_state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Review'),
        ('change_requested', 'Change Requested'),
    ], default='draft')
    classification_done = fields.Boolean("Classification done?",default=False)


    # ===== ALLEGATION INFORMATION =====
    allegation_description = fields.Html(
        string='Allegation Description',
        help="Detailed description of the allegation"
    )

    additional_details = fields.Html(
        string='Additional Details',
        help="Additional Details (if any)"
    )

    allegation_source_id = fields.Many2one('forensic.allegation.source', string='Complaint Source', ondelete='restrict', tracking=True)
    department_id = fields.Many2one(
        'forensic.department',
        string='Department',
        tracking=True,
        ondelete='restrict',
        help="Department responsible for conducting investigation or handling this case"
    )
    directorate_id = fields.Many2one(
        'forensic.directorate',
        string='Directorate',
        tracking=True,
        ondelete='restrict',
        help = "Directorate under which the selected department operates"
    )

    physical_item_ids = fields.One2many(
        comodel_name='complaint.physical.item',
        inverse_name='case_id',
        string="Physical Items Received"
    )

    witness_ids = fields.One2many(
        comodel_name='forensic.case.witness',
        inverse_name='case_id',
        string="Witnesses"
    )

    suspect_ids = fields.One2many(
        comodel_name='forensic.case.suspects',
        inverse_name='case_id',
        string="Suspects",
        help='List of suspects linked to this case.'
    )

    parent_lead_id = fields.Many2one('crm.lead',
        string="Parent Case",
        tracking=True,
        domain="[('active', '=', True), ('id', '!=', id)]",
        help="Parent case of this case."
    )

    child_lead_ids = fields.One2many(
        'crm.lead',
        'parent_lead_id',
        string="Child Cases"
    )

    child_count = fields.Integer(
        string="Child Count",
        compute='_compute_child_count'
    )

    approved_action = fields.Char('Approved Action')

    review_note = fields.Text('Review Note', tracking=True)

    document_line_ids = fields.One2many(comodel_name='forensic.document.line', inverse_name="case_id", string="Document Line")

    # ===== METHODS =====

    can_edit = fields.Boolean('Can Edit', compute='_compute_can_edit', default=True)

    def _compute_can_edit(self):
        user = self.env.user
        can_edit = (
                user.has_group('in2it_forensic_services.group_fcm_review_access') or
                user.has_group('base.group_system') or
                user.has_group('in2it_forensic_services.group_fcm_admin')
        )
        for rec in self:
            rec.can_edit = can_edit

    @api.depends('com_stage_id')
    def _compute_stage_flags(self):
        stage_case_intake = self.env.ref(
            "in2it_forensic_services.common_stage_case_intake", raise_if_not_found=False
        )
        stage_under_review = self.env.ref(
            "in2it_forensic_services.common_stage_under_review", raise_if_not_found=False
        )
        for rec in self:
            rec.is_stage_case_intake = (
                rec.com_stage_id.id == stage_case_intake.id if stage_case_intake else False
            )
            rec.is_stage_under_review = (
                rec.com_stage_id.id == stage_under_review.id if stage_under_review else False
            )

    @api.onchange('directorate_id')
    def _onchange_directorate(self):
        for rec in self:
            rec.department_id = False

    @api.depends('child_lead_ids')
    def _compute_child_count(self):
        for rec in self:
            rec.child_count = len(rec.child_lead_ids)

    @api.model_create_multi
    def create(self, vals_list):
        self = self.with_context(tracking_disable=True, mail_create_nosubscribe=True)
        leads = super().create(vals_list)
        for lead in leads:
            lead._compute_fixed_tag()
            if not lead.internal_coms_ref:
                lead.internal_coms_ref = lead._generate_case_number()

            lead.message_post(
                body="Case created",
                message_type="notification"
            )
        return leads

    def write(self, vals):
        res = super().write(vals)

        # assign tag
        if 'offence_date_to' in vals or 'offence_date_from' in vals:
            self._compute_fixed_tag()

        # -------------------------
        # PREVENT CLOSING PARENT CASE WHEN CHILD ACTIVE
        # -------------------------
        if "active" in vals and vals["active"] is False:
            for lead in self:
                active_children = lead.child_lead_ids.filtered(lambda c: c.active)
                if active_children:
                    raise ValidationError(
                        _(
                            "You cannot close this case because child cases are still active:\n- %s"
                        ) % "\n- ".join(active_children.mapped("name"))
                    )

        return res

    def action_open_case_assignment_wizard(self):
        """Open assignment wizard popup"""
        self.ensure_one()
        if not self.assignment_type_ids:
            case_type_ids = self.env['forensic.assignment.type'].search([]).ids
            case_types = case_type_ids
        else:
            case_types = set(self.assignment_type_ids.ids)
            assigned_types = set(self.case_assignment_ids.mapped('assignment_type_id').ids)
            case_types = list(case_types - assigned_types)

        return {
            'name': (
                'Recommend Case'
                if self.env.context.get('classification_request')
                else 'Assign Case'
            ),
            'type': 'ir.actions.act_window',
            'res_model': 'case.assignment.transient',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_case_id': self.id,
                'assigned_types': case_types,
                'default_assignment_type_ids': None if self.env.context.get('classification_request') else case_types,
            }
        }

    all_assignment_created = fields.Boolean(compute="_compute_hide_review_action_button", store=True)

    @api.depends('assignment_type_ids', 'case_assignment_ids')
    def _compute_hide_review_action_button(self):
        for rec in self:
            all_types = set(rec.assignment_type_ids.ids)
            assigned_types = set(rec.case_assignment_ids.mapped('assignment_type_id').ids)
            if all_types == assigned_types:
                rec.all_assignment_created = True
            else:
                rec.all_assignment_created = False

    def get_relevent_stakeholder_for_submit(self):
        """This function is used to get email of SFO and FO from the governance team."""
        stakeholder_email = set()
        employee = self.env.user.employee_id
        dept_unit_id = employee.department_id.id if employee and employee.department_id else False

        dept_sfo_id = self.env.ref("in2it_forensic_services.senior_forensic_officer", raise_if_not_found=False).id
        dept_fo_id = self.env.ref("in2it_forensic_services.forensic_officer", raise_if_not_found=False).id
        dept_pfo_id = self.env.ref("in2it_forensic_services.principle_of_forensic_officer", raise_if_not_found=False).id

        stakeholder_email = self.env['hr.employee'].search([('department_id','=',dept_unit_id),('job_id','in',[dept_sfo_id,dept_fo_id,dept_pfo_id])]).mapped('work_email')
        email_to = ', '.join(sorted(stakeholder_email))
        return email_to

    def move_to_under_review(self):
        """Move stage to the next, domain for common and sorted by sequence"""
        self.ensure_one()
        stage_under_review = self.env.ref(
            "in2it_forensic_services.common_stage_under_review", raise_if_not_found=False
        )
        if self.review_officer:
            revised_wizard = self.action_revised_case()
            return revised_wizard
        self.com_stage_id = stage_under_review
        self.review_state = 'submitted'

        mail_template = self.sudo().env.ref('in2it_forensic_services.email_template_case_submitted_for_review')
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)


    def action_revised_case(self):
        """Open the revise case wizard"""
        self.ensure_one()
        from_reviewed_officer = self.env.context.get('from_reviewed_officer')
        return {
            'name': "Case Changes Required" if from_reviewed_officer else "Revised Case",
            'type': 'ir.actions.act_window',
            'res_model': 'forensic.case.revise.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_owner_id': self.create_uid.id if from_reviewed_officer else self.review_officer.id,
                'review_state': 'change_requested' if from_reviewed_officer else 'submitted'
            }
        }

    def get_relevent_members(self):
        job_position = self.env.ref('in2it_forensic_services.city_manager', raise_if_not_found=False)
        chief_group = self.env.ref('in2it_forensic_services.group_fcm_case_chief_access', raise_if_not_found=False)
        
        email_to = set()
        # Get manager emails if job_position and review_officer_dept are valid
        if job_position:
            manager_email = self.env['hr.employee'].search([('job_id', '=', job_position.id)]).mapped('work_email')
            email_to.update([email for email in manager_email if email])

        # Get chief emails if chief_group is valid
        if chief_group:
            chief_email = self.env['res.users'].search([('groups_id', '=', chief_group.id)]).mapped('employee_id.work_email')
            email_to.update([email for email in chief_email if email])

        email_to = ','.join(email_to)
        return email_to

    def action_confirmed_case(self):
        """Open the revise case wizard"""
        self.ensure_one()
        stage_reviewed = self.env.ref(
            "in2it_forensic_services.common_stage_reviewed", raise_if_not_found=False
        )
        self.com_stage_id = stage_reviewed
        mail_template = self.sudo().env.ref('in2it_forensic_services.email_template_case_reviewed_submitted_to_chief_and_manager',raise_if_not_found=False)
        if mail_template:
            mail_template.send_mail(self.id, force_send=True)

    def _compute_fixed_tag(self):
        """Assign or replace fixed tags based on offence date and FY."""
        company = self.env.company
        fy_start = company.fy_start_date
        fy_end = company.fy_end_date
        try:
            historic_tag = self.env.ref('in2it_forensic_services.fixed_tag_historic')
            current_tag = self.env.ref('in2it_forensic_services.fixed_tag_current')
            ongoing_tag = self.env.ref('in2it_forensic_services.fixed_tag_ongoing')
        except:
            return  # fail silently so write does not crash

        FIXED_TAGS = {historic_tag.id, current_tag.id, ongoing_tag.id}

        for rec in self:
            # Extract date safely
            offence_to = rec.offence_date_to.date() if rec.offence_date_to else None
            # Determine NEW fixed tag
            if not offence_to:
                new_tag = ongoing_tag
            elif fy_start and offence_to < fy_start:
                new_tag = historic_tag
            elif fy_start and fy_end and fy_start <= offence_to <= fy_end:
                new_tag = current_tag
            else:
                new_tag = None  # no tag change

            if not new_tag:
                continue

            # Check if record already has one of the fixed tags
            existing_fixed = rec.tag_ids.filtered(lambda t: t.id in FIXED_TAGS)

            if existing_fixed:
                # Replace the old fixed tag with new fixed tag
                rec.tag_ids = [
                                  (3, old.id) for old in existing_fixed
                              ] + [(4, new_tag.id)]
            else:
                # No fixed tag yet then add it
                rec.tag_ids = [(4, new_tag.id)]

    @api.onchange('tag_ids')
    def _onchange_restrict_fixed_tag_removal(self):
        for rec in self:

            try:
                historic = self.env.ref('in2it_forensic_services.fixed_tag_historic')
                current = self.env.ref('in2it_forensic_services.fixed_tag_current')
                ongoing = self.env.ref('in2it_forensic_services.fixed_tag_ongoing')
                FIXED_TAGS =  {historic.id, current.id, ongoing.id}
            except:
                return

            original = set(rec._origin.tag_ids.ids)
            current = set(rec.tag_ids.ids)

            # Which fixed tags were removed?
            removed_fixed = (original & FIXED_TAGS) - current

            if removed_fixed:
                # Restore removed fixed tags
                rec.tag_ids = [(4, tag_id) for tag_id in removed_fixed]

                return {
                    'warning': {
                        'title': "Restricted",
                        'message': (
                            "Fixed classification tags cannot be removed.\n"
                            "These tags are determined automatically:\n"
                            "- Historic\n- Current\n- Ongoing"
                        ),
                    }
                }

    @api.model
    def _generate_case_number(self):
        fy = get_financial_year(self.env)  # e.g., "25-26"
        try:
            seq_id = self.env.ref('in2it_forensic_services.seq_forensic_com_case')
        except ValueError:
            raise ValidationError("Sequence for COM case not found.")
        next_num = seq_id.next_by_id()
        return f"{next_num}/{fy}"

    # ===== ACTION METHODS FOR SMART BUTTONS =====

    @api.depends('case_assignment_ids')
    def _compute_case_assignment_count(self):
        for rec in self:
            rec.case_assignment_count = len(rec.case_assignment_ids)
            rec.case_classification_count = len(rec.assignment_type_ids)
            rec.create_investigation_count = len(rec.assignment_type_ids.filtered(lambda r: r.is_project_create))

    def action_open_case_assignments(self):
        self.ensure_one()

        action = self.env.ref('in2it_forensic_services.action_forensic_case_assignment').sudo().read()[0]
        action['domain'] = [('parent_case_id', '=', self.id)]

        # optional: set default parent_case_id when creating new record
        action['context'] = {
            'default_parent_case_id': self.id
        }
        return action

    def action_open_child_leads(self):
        """Opens a list view of all child leads."""
        self.ensure_one()
        return {
            'name': _("Child Leads"),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'views': [(self.env.ref('in2it_forensic_services.view_crm_lead_forensic_list_custom').id, 'list'),
                      (self.env.ref('in2it_forensic_services.view_crm_lead_forensic_form_custom').id, 'form')],
            'res_model': 'crm.lead',
            'domain': [('parent_lead_id', '=', self.id)],
            'context': {'default_parent_lead_id': self.id},
        }

    # -----------------------------
    # VALIDATIONS
    # -----------------------------

    @api.constrains('email_from', 'phone')
    def _check_contact_details(self):
        for rec in self:
            validate_email(rec.email_from)
            validate_phone(rec.phone)

    @api.constrains('offence_date_from', 'offence_date_to')
    def _check_offence_date_range(self):
        for rec in self:
            # Skip validation if fields are empty
            if not rec.offence_date_from:
                raise ValidationError(
                    "Alleged offence start date is missing."
                )

            # Validate: End date must be >= Start date
            if rec.offence_date_to and (rec.offence_date_to < rec.offence_date_from):
                raise ValidationError(
                    "Offence End Date cannot be earlier than Offence Start Date."
                )
            # if not rec.create_date:
            #     if rec.offence_date_from.date() > date.today():
            #         raise ValidationError(
            #             "Alleged offence start date cannot be greater than today's date."
            #         )

            # if rec.create_date and rec.offence_date_from > rec.create_date:
            #     raise ValidationError(
            #         "Alleged offence start date cannot be greater than reporting date."
            #     )

    @api.constrains('parent_lead_id')
    def _check_parent_lead(self):
        for lead in self:
            if not lead.parent_lead_id:
                continue

            parent = lead.parent_lead_id

            if parent.id == lead.id:
                raise ValidationError(_("A case cannot be its own parent."))

            if not parent.active:
                raise ValidationError(_("You can only relate to an active parent case."))

            visited = set()

            def _check_recursion(l):
                if l.id in visited:
                    return True
                visited.add(l.id)
                if l.parent_lead_id:
                    return _check_recursion(l.parent_lead_id)
                return False

            if _check_recursion(parent):
                raise ValidationError(_("Circular parent–child relationships are not allowed."))

    @api.constrains('name')
    def _check_name_alphanumeric(self):
        for lead in self:
            if lead.name and not re.match(r'^[a-zA-Z0-9 ]+$', lead.name):
                raise ValidationError(
                    "Case title must contain only alphanumeric characters."
                )

    @api.depends('internal_coms_ref')
    def _compute_display_name(self):
        """ Compute display name, Reference no will be in dropdown"""
        for rec in self:
            if rec.internal_coms_ref:
                rec.display_name = rec.internal_coms_ref
            else:
                rec.display_name = rec.name or ''


class ResPartnerCRM(models.Model):
    _inherit = 'res.partner'

    is_complainant = fields.Boolean('Is Complainant',
                                default=False,
                                help="Indicates whether this contact is a complainant in a forensic case")

    is_anonymous = fields.Boolean('Is Anonymous',
                                    default=False,
                                    help="Indicates whether this complainant is anonymously identified while reporting")

    complainant_case_ids = fields.One2many(
        'crm.lead',
        'partner_id',
        string='Cases as Complainant',
        help='Cases where this partner is the complainant.'
    )
    directorate_id = fields.Many2one(
        'forensic.directorate',
        string='Directorate',
        tracking=True,
        ondelete='restrict',
        help = "Directorate under which the selected department operates"
    )
    
    @api.constrains('email', 'phone')
    def _check_contact_details(self):
        for rec in self:
            validate_email(rec.email)
            validate_phone(rec.phone)

    @api.constrains('name')
    def _check_name_only_alphabets(self):
        for partner in self:
            if partner.name and not re.match(r'^[A-Za-z ]+$', partner.name):
                raise ValidationError(
                    "Complainant name must contain only alphabets."
                )



class ComplaintPhysicalItem(models.Model):
    _name = 'complaint.physical.item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Physical Items Received"
    _rec_name = "case_id"

    # Link to parent complaint
    case_id = fields.Many2one(
        'crm.lead',
        string="Case",
        ondelete='cascade'
    )
    case_assignment_id = fields.Many2one(
        'forensic.case.assignment',
        string="Case Assignment",
        ondelete='cascade'
    )
    sequence = fields.Integer(default=10, tracking=True)
    item_title = fields.Char("Item Title", required=True, tracking=True)
    item_category = fields.Selection(
        [
            ('electronic', "Electronic Device"),
            ('document', "Document"),
            ('currency', "Currency"),
            ('counterfeit', "Counterfeit Goods"),
            ('storage', "Storage Media"),
        ],
        string="Item Category",
        tracking = True
    )

    quantity = fields.Float("Quantity", tracking=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", tracking=True)

    source = fields.Selection(
        [
            ('complainant', "Complainant"),
            ('witness', "Witness"),
            ('fo', "Field Officer"),
            ('suspect', "Suspect"),
        ],
        string="Source",
        tracking = True
    )

    recovery_location = fields.Char("Recovery Location", tracking=True)
    associated_with = fields.Selection(
        [
            ('victim', "Victim"),
            ('complainant', "Complainant"),
            ('suspect', "Suspect"),
            ('witness', "Witness"),
        ],
        string="Associated With",
        tracking=True
    )

    storage_location = fields.Char("Storage Location", tracking=True)

    current_custodian = fields.Many2one(
        'res.users',
        string="Current Custodian",
        default=lambda self: self.env.user,
        tracking=True
    )

    status = fields.Selection(
        [
            ('custody', "In Custody"),
            ('forensics', "Checked Out to Forensics"),
            ('returned', "Returned to Owner"),
            ('destroyed', "Destroyed"),
        ],
        string="Status",
        default="custody",
        tracking=True
    )

    last_movement_date = fields.Datetime(
        string="Last Movement Date",
        readonly=True,
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'complaint_physical_item_attachment_rel',
        'physical_item_id',
        'attachment_id',
        string="Attachment",
        tracking=True,
    )
    is_from_case = fields.Boolean(string="From case?")


    @api.onchange('status')
    def _update_last_movement_date(self):
        self.last_movement_date = fields.Datetime.now()

    def write(self, vals):
        for rec in self:
            if rec.is_from_case:
                raise UserError("You cannot modify evidence inherited from the case.")
        return super().write(vals)


class ForensicCaseWitness(models.Model):
    _name = 'forensic.case.witness'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Forensic Case Witness"
    _rec_name = "case_id"


    # Link to parent complaint
    case_id = fields.Many2one(
        'crm.lead',
        string="Case",
        ondelete='cascade'
    )
    name = fields.Char("Name", tracking=True)
    email = fields.Char("Email", tracking=True)
    phone = fields.Char("Phone", tracking=True)


    @api.constrains('email', 'phone')
    def _check_contact_details(self):
        for rec in self:
            validate_email(rec.email)
            validate_phone(rec.phone)



class ForensicCaseSuspects(models.Model):
    _name = 'forensic.case.suspects'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Forensic Case Suspects"
    _rec_name = "case_id"


    # Link to parent complaint
    case_id = fields.Many2one(
        'crm.lead',
        string="Case",
        ondelete='cascade'
    )
    name = fields.Char("Name", tracking=True)
    company_name = fields.Char("Company Name", tracking=True)
    email = fields.Char("Email", tracking=True)
    phone = fields.Char("Phone", tracking=True)
    type = fields.Selection([('vendor', 'Vendor'),('employee', 'Employee')],
                           string='Type', tracking=True)
    vendor_emp = fields.Char('Vendor/Employee', tracking=True)



    @api.constrains('email', 'phone')
    def _check_contact_details(self):
        for rec in self:
            validate_email(rec.email)
            validate_phone(rec.phone)


class CrmTag(models.Model):
    _inherit = 'crm.tag'

    is_fixed_tag = fields.Boolean('Is Fixed?',
                                default=False,
                                help="When this tag is set to true, it means the tag is beyond manual intervention.")


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    @api.model_create_multi
    def create(self, vals_list):
        self = self.with_context(tracking_disable=True, mail_create_nosubscribe=True)
        teams = super().create(vals_list)
        for team in teams:
            team.message_post(
                body="Team created",
                message_type="notification"
            )
        return teams
    


class ForensicDocumentation(models.Model):
    _name = 'forensic.document.line'
    _description = 'Forensic Document'
    _rec_name = 'serial_no'

    case_id = fields.Many2one('crm.lead', string="Case")
    case_assignment_id = fields.Many2one('forensic.case.assignment', string="Case Assignment")
    serial_no = fields.Char(
        string="Serial No.",
        readonly=True,
        copy=False,
        default="New"
    )
    description = fields.Text(string="Description")
    document_type_id = fields.Many2one('forensic.document.type', string="Document Type")
    file = fields.Binary(string="File Upload", attachment=True)
    file_name = fields.Char('File Name', copy=False)
    uploaded_by = fields.Many2one('res.users', string="Uploaded By", readonly=True, default=lambda self:self.env.user.id)
    uploaded_date = fields.Datetime(string="Uploaded Date", default=fields.Datetime.now, readonly=True)
    document_stores = fields.Boolean(string="Document Stores")
    document_stores_location = fields.Char(string="Document Stores Location")
    is_annexure = fields.Boolean(string="Is Annexure")
    obtained_by = fields.Char(string="Obtained By",default="EFS")
    obtained_from = fields.Many2one('res.users',string="Obtained From")
    obtained_date = fields.Date(string="Obtained Date")
    is_from_case = fields.Boolean(string="From case?")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('serial_no', 'New') == 'New':
                vals['serial_no'] = self.env['ir.sequence'].next_by_code(
                    'forensic.document.line'
                ) or 'New'
        return super().create(vals_list)
    
    def write(self, vals):
        for rec in self:
            if rec.is_from_case:
                raise UserError("You cannot modify documents inherited from the case.")
        return super().write(vals)

    @api.constrains('obtained_date', 'uploaded_date')
    def _check_obtained_date(self):
        for rec in self:
            if rec.obtained_date and rec.create_date:
                if rec.obtained_date > rec.create_date.date():
                    raise ValidationError(
                        "In Documentation, Obtained Date should be on or before the uploaded date."
                    )
    

class ForensicDocumentType(models.Model):
    _name = 'forensic.document.type'
    _description = 'Document Type'

    name = fields.Char(string="Name")