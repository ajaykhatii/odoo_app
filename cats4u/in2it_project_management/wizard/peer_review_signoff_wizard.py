# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api
from odoo.exceptions import UserError

class PeerReviewSignOffWizard(models.TransientModel):
    _name = 'peer.review.signoff.wizard'
    _description = 'Sign Off Peer Review'

    signature = fields.Binary(string="Signature", required=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Attachments"
    )

    def action_submit(self):
        review_id = self.env.context.get('active_id')

        if not review_id:
            raise UserError("No active review found.")

        review = self.env['forensic.peer.review'].browse(review_id)

        if not self.attachment_ids:
            raise UserError("Please upload attachment before signing.")

        review.write({
            'signature': self.signature,
            'state': 'complete',
            'sign_off_date': fields.date.today(),
            'is_review_complete': True,
            'attachment_ids': [(6, 0, self.attachment_ids.ids)]
        })
        # move project stage ONLY when sign by investigation manager
        review.project_id.write({'report_signoff_date': fields.date.today()})
        review.project_id._move_project_stage()

        return {'type': 'ir.actions.act_window_close'}
