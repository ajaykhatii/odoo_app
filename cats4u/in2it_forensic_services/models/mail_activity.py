# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, _
from odoo.exceptions import UserError


class MailActivity(models.Model):
    _inherit = 'mail.activity'
 
    def _action_done(self, feedback=False, attachment_ids=None):
        """Intercept Mark as Done triggered from JS"""
 
        res_models = ['crm.lead','forensic.case.assignment','project.project']
        if self.env.user.has_group('base.group_system') or self.env.user.has_group('in2it_forensic_services.group_fcm_admin'):
            return super()._action_done(feedback=feedback, attachment_ids=attachment_ids)
 
        for activity in self:
            if activity.res_model in res_models:
                record = self.env[activity.res_model].browse(activity.res_id)                
                if record.user_id != self.env.user:
                    raise UserError("Only the assigned user can mark this done.")
 
        return super()._action_done(feedback=feedback, attachment_ids=attachment_ids)