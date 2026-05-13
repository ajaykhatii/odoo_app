# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ForensicReviseWizard(models.TransientModel):
    _name = 'forensic.case.revise.wizard'
    _description = 'Forensic Revise Case Wizard'

    lead_id = fields.Many2one("crm.lead", required=True, readonly=True)
    owner_id = fields.Many2one("res.users", required=True)
    note = fields.Text("Notes")

    activity_id = fields.Many2one("mail.activity", readonly=True)

    def action_submit(self):
        """Create a new Todo activity when submit is clicked"""
        self.ensure_one()

        activity_values = {
            "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
            "res_id": self.lead_id.id,
            "res_model_id": self.env['ir.model']._get_id("crm.lead"),
            "user_id": self.owner_id.id,
            "summary": "Revised Case Activity",
            "note": self.note,
        }

        if self.env.context.get('review_state') == 'change_requested':
            self.lead_id.review_state = 'change_requested'
        else:
            self.lead_id.review_state = 'submitted'


        self.env["mail.activity"].with_context(
            mail_create_nosubscribe=True,
            mail_activity_quick_update=True
        ).create(activity_values)

        if self.lead_id.review_officer:
            # this mail is operated by specialist clerk to sfo, fo
            mail_template = self.sudo().env.ref('in2it_forensic_services.email_template_case_submitted_for_review_after_update')
            if mail_template:
                mail_template.send_mail(self.lead_id.id, force_send=True)
                for activity in self.lead_id.activity_ids:
                    if activity.summary == 'Revised Case Activity':
                        activity.action_done()

        else:
            # this mail is operated sfo, fo to specialist clerk 
            ctx = {'email_to': self.owner_id.employee_id.work_email or ''}
            mail_template = self.sudo().env.ref('in2it_forensic_services.email_template_case_submitted_for_udate')
            if mail_template:
                self.lead_id.review_officer = self.env.uid
                mail_template.with_context(ctx).send_mail(self.lead_id.id, force_send=True)

        return {'type': 'ir.actions.act_window_close'}

