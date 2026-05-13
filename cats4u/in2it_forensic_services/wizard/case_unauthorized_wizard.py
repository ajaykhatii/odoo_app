from odoo import api, fields, models
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification

class CaseUnauthorizedWizard(models.TransientModel):
    _name = "case.unauthorized.wizard"
    _description = "Case Unauthorized Wizard"

    case_assignment_id = fields.Many2one('forensic.case.assignment', string="Case")
    reason = fields.Char("Reason")

    def stakeholder_team(self):
        dept_sfo_id = self.env.ref("in2it_forensic_services.group_fcm_case_sfo_access", raise_if_not_found=False).id
        dept_fo_id = self.env.ref("in2it_forensic_services.group_fcm_case_fo_access", raise_if_not_found=False).id
        users = self.env['res.users'].search([('groups_id', 'in', [dept_sfo_id,dept_fo_id])])
        return users

    def action_case_unauthorized(self):
        unauthorise_stage_id = self.env.ref('in2it_forensic_services.case_type_stage_reject')
        if unauthorise_stage_id:
            self.case_assignment_id.write({'stage_id': unauthorise_stage_id.id, 'is_unauthorized': True, 'reason': self.reason})
            
            if self.case_assignment_id.assignment_type_id in [self.env.ref('in2it_forensic_services.assignment_type_line_refferal'),
                                            self.env.ref('in2it_forensic_services.assignment_type_spk_for'),
                                            self.env.ref('in2it_forensic_services.assignment_type_spk_rec'),
                                            self.env.ref('in2it_forensic_services.assignment_type_eth'),
                                            self.env.ref('in2it_forensic_services.assignment_type_dfo'),
                                            self.env.ref('in2it_forensic_services.assignment_type_lsa'),
                                            self.env.ref('in2it_forensic_services.assignment_type_forensic')]:
                mail_template = self.sudo().env.ref('in2it_forensic_services.email_template_case_type_unauthorized')
                if mail_template:
                    mail_template.send_mail(self.case_assignment_id.id, force_send=True)
                    users = self.stakeholder_team()
                    
                    for user in users:
                        message = f'Case { self.case_assignment_id.parent_case_id.name } has been marked as Not Authorised by the City Manager.'
                        user_id = user.id
                        res_id = self.case_assignment_id.id
                        model = self.case_assignment_id._name
                        if user_id and res_id and model:
                            send_system_notification(self.env,message,model,user_id,res_id)
            
            if self.case_assignment_id.assignment_type_id == self.env.ref('in2it_forensic_services.assignment_type_rec'):
                mail_template = self.sudo().env.ref('in2it_forensic_services.email_template_rec_case_type_not_authorized')
                if mail_template:
                    mail_template.send_mail(self.case_assignment_id.id, force_send=True)

                    users = self.stakeholder_team()
                    for user in users:
                        message = f'REC Case { self.case_assignment_id.parent_case_id.name } has been marked Not Authorized by the City Manager as it falls outside the applicable jurisdiction. The case has been moved to Line Referral for further action. Please review.'
                        user_id = user.id
                        res_id = self.case_assignment_id.id
                        model = self.case_assignment_id._name
                        if user_id and res_id and model:
                            send_system_notification(self.env,message,model,user_id,res_id)

