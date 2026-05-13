# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json

class ForensicTeam(models.TransientModel):
    _name = 'forensic.team.wizard'
    _description = 'Forensic Team'


    project_id = fields.Many2one('project.project', string="Project")
    project_investigator_ids = fields.Many2many(
        'res.users', string='Lead Investigator',
        help='Investigator must be selected from investigation team members only.')
    
    forensic_member_ids = fields.One2many(
        comodel_name='forensic.investigation.team.wizard',
        inverse_name='case_assignment_id',
        string="Investigation Members",
        help='List of investigation members linked to this case.'
    )

    li_domain = fields.Char()


    def send_mail_notification(self,assign_forensic_team):
            role_template = self.env.ref(
                'in2it_project_management.mail_template_investigation_team_assignment',
                raise_if_not_found=False
            )

            emails = []

            team_members = assign_forensic_team.forensic_member_ids.mapped('member_ids')
            emails.extend(
                user.email for user in team_members if user.email
            )
            emails = list(set(emails))
            
            if emails and role_template:
                role_template.with_context(members=",".join(team_members.mapped('name'))).send_mail(assign_forensic_team.id,
                    force_send=True,
                    email_values={'email_to': ",".join(emails),
                    }
                )
            
            lead_emails = []
            lead_investigators = assign_forensic_team.project_investigator_ids
            lead_emails.extend(
                user.email for user in lead_investigators if user.email
            )
            lead_emails = list(set(lead_emails))
           
            if lead_emails and role_template:
                role_template.with_context(members=",".join(lead_investigators.mapped('name')),
                    investigator="Lead Investigator").send_mail(
                    assign_forensic_team.id,
                    force_send=True,
                    email_values={
                        'email_to': ",".join(lead_emails),
                    }
                )


    def send_system_notification(self,assign_forensic_team):
          #System Notification
        model = assign_forensic_team.project_id._name
        if model:
            res_model_id = self.env['ir.model'].search([('model','=',model)])
        for user in assign_forensic_team.forensic_member_ids.mapped('member_ids'):
            if res_model_id:
                    
                job_name = user.employee_id.job_id.name if user.employee_id and user.employee_id.job_id else ''
                self.env['system.notification'].create({
                    'message':f"New Investigation Assignment - Case { assign_forensic_team.project_id.name } has been assigned to you as {job_name}",
                    'user_id':user.id,
                    "res_model_id":res_model_id.id or False,
                    "res_id": assign_forensic_team.project_id.id
                })
        for lead_investigator in assign_forensic_team.project_investigator_ids:
            self.env['system.notification'].create({
                    'message':f"New Investigation Assignment - Case { assign_forensic_team.project_id.name } has been assigned to you as Lead Investigator",
                    'user_id':lead_investigator.id,
                    "res_model_id":res_model_id.id or False,
                    "res_id": assign_forensic_team.project_id.id
                })
            

    @api.onchange('forensic_member_ids')
    def _compute_li_domain(self):
        for rec in self:
            rec.li_domain = json.dumps([('id','=',False)])
            if rec.forensic_member_ids:
                ids_list = rec.forensic_member_ids.mapped('member_ids').ids
                rec.li_domain = json.dumps([('id', 'in', ids_list)])

    def action_create_forensic_team(self):
        for rec in self:
            if not rec.project_investigator_ids:
                raise ValidationError("Forensic Team Required.")
            
            vals = {
                'project_id':self.project_id.id,
                'project_investigator_ids': [(6, 0, rec.project_investigator_ids.ids)],
                'forensic_member_ids': [
                    (0, 0, {
                        'unit_id': s.unit_id.id if s.unit_id else False,
                        'job_id': s.job_id.id if s.job_id else False,
                        'member_ids': [(6, 0, s.member_ids.ids)],
                    })
                    for s in rec.forensic_member_ids
                ],
            }

            assign_forensic_team = self.env['assigned.forensic.team']\
            .with_context(li_domain=rec.li_domain)\
            .create(vals)

            assign_forensic_team.project_id.assigned_forensic_team_id = assign_forensic_team.id
            # Notification Template
           
            self.send_mail_notification(assign_forensic_team)        
            self.send_system_notification(assign_forensic_team)


    @api.constrains('forensic_member_ids', 'project_investigator_ids')
    def _check_investigation_member(self):
        for rec in self:
            #  invalid_leads means members who is removed from investigation line but set as let investigator
            valid_members = rec.forensic_member_ids.mapped('member_ids')
            invalid_leads = rec.project_investigator_ids - valid_members

            if invalid_leads:
                raise ValidationError(_(f"{', '.join(invalid_leads.mapped('name'))} member is part of the Lead Investigator Team. \nRemove them from Lead Investigator first."))
            
            if rec.project_investigator_ids:
                forensic_mem_ids = rec.forensic_member_ids.mapped('member_ids').ids
                if rec.project_id.user_id and forensic_mem_ids:
                    if rec.project_id.user_id.id in forensic_mem_ids:
                        raise ValidationError("Investigation manager cannot be a part of Investigation Team.")
                


            manager_id = self.env.ref('in2it_forensic_services.manager')
            pfo_id = self.env.ref('in2it_forensic_services.principle_of_forensic_officer')

            job_id_manager_count = 0
            job_id_pfo_count = 0
            for team in self.forensic_member_ids:
                investigation_team = self.env['forensic.investigation.team'].search(
                    [('id', '!=', team.id),('case_assignment_id','=',team.case_assignment_id.id),('job_id', '=', team.job_id.id),
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


class ForensicInvestigationTeamWizard(models.TransientModel):
    _name = 'forensic.investigation.team.wizard'
    _description = 'Forensic Investigation Team Wizard'

    case_assignment_id = fields.Many2one('forensic.team.wizard', string='Case Assignment', ondelete='cascade')
    unit_id = fields.Many2one('hr.department', 'Unit')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    job_id = fields.Many2one('hr.job', string='Job Position')
    member_ids = fields.Many2many('res.users', string='Members')


    

    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        self.job_id = False
        self.member_ids = False

    @api.onchange('job_id')
    def _onchange_job_id(self):
        self.member_ids = False

    @api.constrains('case_assignment_id', 'unit_id', 'job_id')
    def _check_unique_unit_job_per_case(self):
        for record in self:
            if not record.case_assignment_id or not record.unit_id or not record.job_id:
                continue

            domain = [
                ('case_assignment_id', '=', record.case_assignment_id.id),
                ('unit_id', '=', record.unit_id.id),
                ('job_id', '=', record.job_id.id),
                ('id', '!=', record.id),
            ]

            if self.search_count(domain):
                raise ValidationError(_(
                    "The Job Position '%s' is already assigned to Unit '%s' "
                    "for this Investigation Team. Duplicate entries are not allowed."
                ) % (record.job_id.display_name, record.unit_id.display_name))