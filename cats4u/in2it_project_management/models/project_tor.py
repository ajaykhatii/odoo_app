from odoo import models, fields, api, _
import json
from odoo.exceptions import ValidationError


class InvestigationVendorTor(models.Model):
    _name = 'investigation.vendor.tor'
    _description = "Pricing Schedule"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'project_id'

    terms_of_reference = """
                            The following deliverables must be complied with by the Consultant when they manage, investigate and report on their findings.  The successful Consultant will, where necessary, incorporate other commercial forensic consultants and experts into a multidisciplinary team which they will manage and direct. 
                        """
    
    engage_work_programme = """
                            <p>2.1 The responsible partner/director who will lead this assignment and sign off the final report must meet on a weekly basis (at a time and day to be determined by the City) with the Chief: Ethics and Forensic Services and/or the CCT appointed Contract/Project Manager.</p>
                            <p>2.2 Please note that interviews with Councillors/Employees of the CCT should be arranged via the CCT appointed Contract/Project Manager.</p>
                            <p>2.3 All documentation relating to this project remains the property of the CCT and must be submitted to the CCT on completion of the project.</p>
                            <p>2.4 All City equipment, electronic devices, documentation and any other property acquired in and during this mandate for which the CCT is invoiced remains the property of the CCT and Consultant undertakes to return same on the completion of the assignment.</p>
                            <p>2.5 All intellectual property and copyright in whatever form (inclusive of the report) resulting from this assignment, remains and/or will become the sole property of the CCT.</p>
                            <p>2.6 Consultant undertakes not to make use (for training or any other purpose) of any information obtained during this assignment in any manner during and/or post the conclusion of the assignment without the express written approval of the Chief: Ethics and Forensic Services.</p>
                            <p>2.7 Consultant is expressly prohibited from engaging with the media, both during the review/investigation and also post the completion of same, with regard to any matter relating to this brief unless written approval has been granted by the Chief: Ethics and Forensic Services.</p>
                        """
    
    engage_time_frame = """
                            <p>3.1 This project will take place on a date to be announced by the Chief: Ethics and Forensic Services.</p>
                           <p>3.2 It is required that this project must be completed within a six-week timeframe from the date of appointment.</p>
                        """
    
    team_delivering_service = """
                               <p>4.1 ​The proposal must include the names of the team members who will be working on the project as provided in the panel member’ tender submission for Tender 087C/2023/24.</p>
                               <p>4.2 The panel members must inform the City of any amendments to the team presented in their tender submission providing a reason for such amendments. The panel members must include the CV of any team member that may be a replacement to a team member as provided in Tender 087C/2023/24, for evaluation.</p>
                               <p>4.3 As stipulated in Tender 087C/2023/24, if the amendments to the team have the effect of the Consultant no longer meeting the requirements set out in the tender document pertaining to the qualifications, skill and experience, the CCT has the right not to request further service from that Consultant for the duration of the contract.</p>
                            """

    

    project_id = fields.Many2one('project.project', string="Project", store=True)
    case_id = fields.Many2one('crm.lead',related='project_id.case_id')
    name = fields.Char(string="Case Title",related="case_id.name")
    directorate_id = fields.Many2one('forensic.directorate', string="Directorate", related='case_id.directorate_id')
    department_id = fields.Many2one('forensic.department', string="Department", related='case_id.department_id')
    assignment_id = fields.Many2one('forensic.case.assignment', string="Case Assignment", related="project_id.assignment_id")
    allegation_nature_id = fields.Many2one(related="assignment_id.allegation_nature_id")
    create_date = fields.Datetime(related="project_id.create_date",string="Authorization Date")
    status = fields.Selection([('draft','Draft'),('to_approve','To Approve'),('approved','Approved')],default="draft",string="Status",tracking=True)
    terms_of_reference = fields.Html(string="Terms of Reference",default=terms_of_reference)
    engage_work_programme = fields.Html(string="Engagement Work Programme",default=engage_work_programme)
    engage_time_frame = fields.Html(string="Engagement Time Frame",default=engage_time_frame)
    team_delivering_service = fields.Html(string="Team Delivering Phase",default=team_delivering_service)
    submission_req_closure_date_time = fields.Html(string="Submission Requirements and Closure Date and Time")
    pricing_schedule_ids = fields.One2many("schedule.pricing",'pricing_id',string="Pricing Schedule")
    pricing_schedule_item_ids = fields.One2many("pricing.schedule.item",'pricing_item_id',string="Pricing Schedule Item")
    currency_id = fields.Many2one('res.currency',related="project_id.currency_id",string="Currency")
    price_subtotal = fields.Monetary(string="SUB-TOTAL",currency_field='currency_id',compute="_compute_amounts",
    store=True,tracking=True)
    price_subtotal1 = fields.Monetary(string="Subtotal",currency_field='currency_id',compute="_compute_amounts",store=True,tracking=True)
    vat_amount = fields.Monetary(
        string="VAT (15%)",
        currency_field="currency_id",
        compute="_compute_amounts",
        store=True
    )
    total_amount = fields.Monetary(
        string="TOTAL PRICE (INCLUDING VAT)",
        currency_field="currency_id",
        compute="_compute_amounts",
        store=True,tracking=True
    )
    approval_action = fields.Selection([('investigation_manager', 'Investigation Manager'),
                                       ('chief', 'Chief'),
                                       ('ed', 'Executive Officer'),('complete', 'Complete'),], string="Approval Action")
    
    tor_line_ids = fields.One2many('tor.comment.line', 'tor_id', string="TOR Comments")
    user_id = fields.Many2one('res.users', string="Pending Approval")
    pfo_id = fields.Many2one('res.users',
        default='project_id.assigned_pfo_id.id',
        store=True,
    )



    approver_line_ids = fields.One2many('tor.approver.line', 'tor_id', string="TOR Approver(s)")
    
    @api.onchange('pricing_schedule_ids')
    def action_pfo_id(self):
        for rec in self:
            if rec.project_id:
                rec.pfo_id = rec.project_id.assigned_pfo_id.id
                rec.submission_req_closure_date_time = f"""
                    <p>5.1 Consultant must submit the requirements as outlined above and as per the provision of the 087C/2023/24.</p>
                    <p>5.2 Consultant is required to prepare a proposal in accordance with the fees as detailed in the Consultants proposal in respect of 087C/2023/24.</p>
                    <p>5.3 Consultant is required to provide the CCT with a breakdown of the fees and/or other costs charged as well as a breakdown of the skill sets (e.g. attorney, accounting, auditing), levels (e.g. years of experience) and anticipated hours that will be spent on the assignment, by each such team member.</p>
                    <p>5.5 It should be noted that items (4), (5), (6) and (7) although included in the pricing schedule will only be paid for if requested / required during this engagement.</p>
                    <p>5.6 Where the Consultant is required to specify rates applicable to non-legal commercial forensic experts and/or professionals whose services will be used, the percentage mark-up should be in line with the fee structure applicable to the relevant professional or expert’s field as per the provisions in the tender and contract.</p>
                    <p>5.7 Consultants must submit a detailed project proposal and plan for the completion of this project linked to the terms of reference, a detailed methodology, with clear deliverable milestones and timeframes as per City requirements outlined, linked to budget and resources.</p>
                    <p>5.8 Any additional relevant information related to the project plan and pertinent to the implementation of the project to match the City’s requirements is to be included.</p>
                    <p>5.9 In terms of 087C/2023/24, the Consultant has 48 hours from the time the instruction was sent to accept or decline the assignment. The consultant must acknowledge receipt of the instruction.</p>
                    <p>5.10 On accepting the assignment, within seven calendar days, the consultant must provide a detailed project plan, including the resources to be used on the assignment and prices to ensure to the satisfaction of the CCT that the tenderer has sufficient capacity, experience and expertise to conclude the assignment and that the assignment has been appropriately priced.  (Refer to Section 2.1.5.2 of the signed MOA).</p>
                    <p>5.11 Submissions are to be sent to the City of Cape Town contact person:</p>
                    <div style="margin-left:20px;">
                        {self.project_id.assigned_pfo_id.email}
                        <br/>
                        {self.project_id.user_id.email}
                    </div>
                    <br/>
                    <p>5.12 Please note: no company profiles or similar are required.  Due to CCT email document size restrictions – service providers are requested to ensure that their submission documents do not exceed a total of 4 MB or if larger documents are sent these are sent in clearly marked, separate emails.</p>
                    <p>5.13 For technical/SCM questions on the specifications please contact:</p>
                    <div style="margin-left:20px;">
                        {self.pfo_id.name} (Technical)
                        <br/>
                        Principal Forensic Officer: Forensic Services
                        <br/>
                        E-mail: {self.pfo_id.email}
                        <br/>
                        <br/>
                        <p>We look forward to your response.</p>
                    </div>
                """

    def unlink(self):
        for record in self:
            if record.status != 'draft':
                raise ValidationError("You can only delete records in Draft state.")
        return super().unlink()

    def _compute_access_url(self):
        super()._compute_access_url()
        for tor in self:
            tor.access_url = f'/my/tors/{tor.id}'


    @api.depends('pricing_schedule_ids.total','pricing_schedule_item_ids.total')
    def _compute_amounts(self):
        for rec in self:
            subtotal1 = sum(rec.pricing_schedule_ids.mapped('total'))
            rec.price_subtotal1 = subtotal1

            subtotal = sum(rec.pricing_schedule_item_ids.mapped('total')) + subtotal1
            vat = subtotal * 0.15

            rec.price_subtotal = subtotal
            rec.vat_amount = vat
            rec.total_amount = subtotal + vat


    @api.constrains('project_id')
    def _check_unique_project_tor(self):
        for rec in self:
            if rec.project_id:
                tor = self.search([
                    ('project_id', '=', rec.project_id.id),
                    ('id', '!=', rec.id)
                ])
                if tor:
                    raise ValidationError(
                        "Only one TOR can be created for this project."
                    )
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        descriptions = [
            "Planning Phase",
            "Investigation Phase",
            "Reporting Phase",
        ]
        lines = [(0, 0, {'item': i + 1, 'description': desc}) for i, desc in enumerate(descriptions)]
        res['pricing_schedule_ids'] = lines
        return res
    
    
    @api.onchange('pricing_schedule_item_ids')
    def _onchange_price_schedule_items(self):
        num = 4
        for rec in self.pricing_schedule_item_ids:
            rec.item = num
            num += 1

    # pfo send tor for approval to investigation manager
    def send_tor_for_approval(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for rec in self:
            if not rec.project_id.user_id:
                raise ValidationError("Investigation manager not assigned in case investigation.")

            if not rec.project_id.assigned_pfo_id:
                raise ValidationError("PFO not assigned in case investigation.")
            
            if user != rec.project_id.assigned_pfo_id and not is_admin:
                raise ValidationError(
                    "You do not have access to send TOR for approval. Only PFO or Admin can send the request."
                )

            if is_admin or ( user.has_group('in2it_forensic_services.group_fcm_case_pfo_access') and \
                user.employee_id.job_id == self.env.ref('in2it_forensic_services.principle_of_forensic_officer') and \
                user == rec.project_id.assigned_pfo_id):

                return {
                    'name' : 'Send Tor For Approval',
                    'view_mode' : 'form',
                    'type' : 'ir.actions.act_window',
                    'res_model' : 'tor.remark.wizard',
                    'target' : 'new',
                    'context' : {
                        'default_tor_id' : rec.id,
                        'default_pfo_id' : rec.project_id.assigned_pfo_id.id,
                        'send_tor' : True
                    }
                }
            else:
                raise ValidationError("Please check your user configuration.Your job position and group should have PFO.")
                       
    def action_send_for_update(self):
        for rec in self:
            return {
                'name' : _('Send For Update'),
                'view_mode' : 'form',
                'type' : 'ir.actions.act_window',
                'res_model' : 'tor.remark.wizard',
                'target' : 'new',
                'context' : {
                    'default_tor_id' : self.id,
                    'update' : True,
                    'is_remark' : True
                }
            }
    
    # pfo send tor for approval to investigation manager
    def action_approve_tor(self):
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for rec in self:
            if not is_admin and user != rec.user_id:
                raise ValidationError("You do not have access.")
            
            return {
                    'name' : 'Send Tor For Approval',
                    'view_mode' : 'form',
                    'type' : 'ir.actions.act_window',
                    'res_model' : 'tor.remark.wizard',
                    'target' : 'new',
                    'context' : {
                        'default_tor_id' : rec.id,
                        'approve' : True
                    }
                }
            

    @api.model_create_multi
    def create(self, vals_list):

        user = self.env.user
        is_admin = user.has_group('base.group_system')
        for vals in vals_list:
            project = self.env['project.project'].browse(vals.get('project_id'))
            if project:
                if not (is_admin or user == project.assigned_pfo_id):
                    raise ValidationError("Only Admin or Assigned PFO can create this record.")

        return super().create(vals)
    

    def write(self, vals):
        if self.env.context.get('bypass_pfo_check'):
            return super().write(vals)
        
        if self.env.user.has_group('base.group_portal'):
            return super().write(vals)

        user = self.env.user
        is_admin = user.has_group('base.group_system')

        for rec in self:
            if not (is_admin or user == rec.project_id.assigned_pfo_id):
                raise ValidationError("Only Admin or Assigned PFO can edit this record.")

        return super().write(vals)

    def action_print_vendor_report(self):
        return self.env.ref(
            'in2it_project_management.vendor_accept_tor_report_action'
        ).report_action(self)


    def get_signature_and_timestamp(self):
        self.ensure_one()

        approvers = self.approver_line_ids.sorted('create_date', reverse=True)

        def get_data(role):
            rec = approvers.filtered(lambda r: r.approval_action == role)[:1]
            if not rec:
                return False

            sign = rec.user_id.sudo().sign_signature
            if sign:
                sign = sign.decode()

            return {
                'name': rec.user_id.name,
                'user_id': rec.user_id.id,
                'sign': sign,
                'date': rec.date,
            }

        return {
            'im': get_data('investigation_manager'),
            'chief': get_data('chief'),
            'ed': get_data('ed'),
        }

class SchedulePricing(models.Model):
    _name = "schedule.pricing"
    _description = "Schedule Pricing"


    pricing_id = fields.Many2one('investigation.vendor.tor',string="Pricing Schedule")
    item = fields.Integer(string="Item")
    description = fields.Char(string="Description")
    hourly_rate = fields.Float(string="Hourly Rate", digits=(16, 2))
    estimated_rate = fields.Float(string="Estimated Hours", digits=(16, 2))
    currency_id = fields.Many2one(
        'res.currency',
        related='pricing_id.currency_id',
        store=True,
        readonly=True
    )

    total = fields.Monetary(
        string="Total",
        currency_field='currency_id',
        compute="_compute_total",
        store=True,
    )

    @api.depends('hourly_rate', 'estimated_rate')
    def _compute_total(self):
        for line in self:
            line.total = line.hourly_rate * line.estimated_rate
            

    @api.constrains('hourly_rate', 'estimated_rate')
    def _check_positive_values(self):
        for rec in self:
            if rec.hourly_rate < 0:
                raise ValidationError("Hourly Rate cannot be negative.")
            if rec.estimated_rate < 0:
                raise ValidationError("Estimated Hours cannot be negative.")


class PricingScheduleItem(models.Model):
    _name = "pricing.schedule.item"
    _description = "Pricing Schedule Items"

    pricing_item_id = fields.Many2one('investigation.vendor.tor',string="Pricing Schedule")
    item = fields.Integer(string="Item")
    description = fields.Char(string="Description")
    hourly_rate = fields.Float(string="Hourly Rate", digits=(16, 2))
    estimated_rate = fields.Float(string="Estimated Hours", digits=(16, 2))
    currency_id = fields.Many2one(
        'res.currency',
        related='pricing_item_id.currency_id',
        store=True,
        readonly=True
    )

    total = fields.Monetary(
        string="Total",
        currency_field='currency_id',
        compute="_compute_total",
        store=True,
    )

    @api.depends('hourly_rate', 'estimated_rate')
    def _compute_total(self):
        for line in self:
            line.total = line.hourly_rate * line.estimated_rate


    @api.constrains('hourly_rate', 'estimated_rate')
    def _check_positive_values(self):
        for rec in self:
            if rec.hourly_rate < 0:
                raise ValidationError("Hourly Rate cannot be negative.")
            if rec.estimated_rate < 0:
                raise ValidationError("Estimated Hours cannot be negative.")
            
    
            

class TorCommentLine(models.Model):
    _name = 'tor.comment.line'
    _description = 'Tor Comment Line'

    tor_id = fields.Many2one('investigation.vendor.tor', string="TOR")
    sender_id = fields.Many2one('res.users', string="User By")
    recipient_id = fields.Many2one('res.users', string="Sent To")
    sent_date = fields.Datetime(string="Date")
    remark = fields.Text(string="Remarks")

class TorApproverLine(models.Model):
    _name = 'tor.approver.line'
    _description = 'TOR Approver(s)'

    tor_id = fields.Many2one('investigation.vendor.tor', string="TOR")
    user_id = fields.Many2one('res.users', string="User")
    job_id = fields.Many2one('hr.job', string="Job position")
    date = fields.Datetime(string="Date")
    remark = fields.Text(string="Remarks")
    status = fields.Selection([('send_for_update','Send For Updates'),('approved','Approved')], string="Status")
    approval_action = fields.Selection([('investigation_manager', 'Investigation Manager'),('chief','Chief'), ('ed','Executive Officer')])
