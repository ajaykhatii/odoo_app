# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields
from odoo.exceptions import ValidationError
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification

class TorRemarkWizard(models.Model):
    _name = 'tor.remark.wizard'
    _description = 'TOR Remark Wizard'

    tor_id = fields.Many2one('investigation.vendor.tor', string="Investigation Vendor Tor")
    remark = fields.Text(string="Remark")
    user_id = fields.Many2one('res.users', string="User", default=lambda self : self.env.user.id)

    date = fields.Datetime(string="Date", default=fields.datetime.now())

    # step-1 from pfo
    def send_tor_for_approval_wizard(self):
        for rec in self:
            rec.tor_id.status = 'to_approve'
            rec.tor_id.approval_action = 'investigation_manager'
            rec.tor_id.user_id = rec.tor_id.project_id.user_id.id

            rec.tor_id.message_post(
            body=(f"Request sent to : {rec.tor_id.project_id.user_id.name}"),
            message_type="comment")

            tor_comment_vals = {
                'sender_id': self.env.user.id,
                'recipient_id':rec.tor_id.user_id.id,
                'sent_date':fields.datetime.now(),
                'remark':rec.remark
            }
            rec.tor_id.write({
                'tor_line_ids': [(0, 0, tor_comment_vals)]
            })
            message = "TOR request waiting for your approval"
            user_id = rec.tor_id.project_id.user_id.id
            res_id = rec.tor_id.id
            model = rec.tor_id._name
            if user_id and res_id and model:
                send_system_notification(self.env,message,model,user_id,res_id)

    
    # Step-2 from investigaiton manager and chief and ed
    def action_approve_tor_wizard(self):
        for rec in self:
            user = self.env.user
            is_admin = user.has_group('base.group_system')

            if (is_admin or user == rec.tor_id.user_id):
                if rec.tor_id.approval_action == 'investigation_manager':
                    rec.tor_id.message_post(
                        body=(f"Request sent to : {rec.tor_id.project_id.chief_id.name}"),
                        message_type="comment")
                    rec.tor_id.user_id = rec.tor_id.project_id.chief_id.id
                    rec.tor_id.approval_action = 'chief'
                    line_approval_action = 'investigation_manager'
                    
                    message = "TOR request waiting for your approval"
                    user_id = rec.tor_id.project_id.chief_id.id
                    res_id = rec.tor_id.id
                    model = rec.tor_id._name
                    if user_id and res_id and model:
                        send_system_notification(self.env,message,model,user_id,res_id)

                elif rec.tor_id.approval_action == 'chief':
                    if not rec.tor_id.project_id.directorate_id.ed_officer_id.id:
                        raise ValidationError("Executive Officer not assign.")

                    rec.tor_id.message_post(
                        body=(f"Request sent to : {rec.tor_id.project_id.directorate_id.ed_officer_id.name}"),
                        message_type="comment")
                    rec.tor_id.user_id = rec.tor_id.project_id.directorate_id.ed_officer_id.id
                    rec.tor_id.approval_action = 'ed'
                    line_approval_action = 'chief'
                
                else:
                    raise ValidationError("You do not have access to send TOR for approval")
                
                # TOR LOG COMMENT FOR APPROVAL AND SEND FOR UPDATES
                tor_comment_vals = {
                    'sender_id': self.env.user.id,
                    'recipient_id':rec.tor_id.user_id.id,
                    'sent_date':fields.datetime.now(),
                    'remark':rec.remark,
                }

                emp_id = self.env['hr.employee'].search([('user_id','=',self.env.user.id)], limit=1)
                # TOR APPROVER(S)
                tor_approver_vals = {
                    'user_id': self.env.user.id,
                    'job_id' : emp_id.job_id.id,
                    'status':"approved",
                    'date':fields.datetime.now(),
                    'remark':rec.remark,
                    'approval_action':line_approval_action,
                }

                rec.tor_id.write({
                    'tor_line_ids': [(0, 0, tor_comment_vals)],
                    'approver_line_ids': [(0, 0, tor_approver_vals)]
                })

    def action_send_for_update(self):
        for rec in self:
            if rec.remark:
                rec.tor_id.status = 'draft'
                rec.tor_id.approval_action = False
                rec.tor_id.user_id = rec.tor_id.project_id.assigned_pfo_id.id
                rec.tor_id.message_post(
                body=(f"Send for Update : {rec.remark}"),
                message_type="comment")

                tor_comment_vals = {
                    'sender_id': self.env.user.id,
                    'recipient_id':rec.tor_id.user_id.id,
                    'sent_date':fields.datetime.now(),
                    'remark':rec.remark,
                }
                rec.tor_id.write({
                    'tor_line_ids': [(0, 0, tor_comment_vals)]
                })

                message = "TOR request waiting for your update"
                user_id = rec.tor_id.user_id.id
                res_id = rec.tor_id.id
                model = rec.tor_id._name
                if user_id and res_id and model:
                    send_system_notification(self.env,message,model,user_id,res_id)

        
