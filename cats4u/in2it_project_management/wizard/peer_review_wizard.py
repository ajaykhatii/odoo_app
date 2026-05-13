# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields
from odoo.exceptions import UserError, ValidationError
class PeerReviewChangeWizard(models.TransientModel):
    _name = 'peer.review.change.wizard'
    _description = 'Peer Review Change Wizard'

    comment = fields.Text(string="Comment", required=True)

    def action_submit(self):
        review_id = self.env.context.get('active_id')
        if not review_id:
            raise UserError("Peer review record not found.")

        review = self.env['forensic.peer.review'].browse(review_id)
        if review.assignment_type == 'internal':
            review.write({'state': 'in_progress'})
        user_lines = review.line_ids.filtered(
            lambda l: l.user_id.id == self.env.uid
        )
        pending_line = user_lines.filtered(lambda l: l.action == 'pending')
        if pending_line:
            line = pending_line[0]
            line.write({
                'action': 'changes_required',
                'comment': self.comment,
                'date': fields.Datetime.now()
            })
            review._send_review_notifications()

        else:
            last_line = user_lines.sorted('date')[-1]

            review.env['forensic.peer.review.line'].create({
                'review_id': review.id,
                'user_id': self.env.user.id,
                'action': 'changes_required',
                'comment': self.comment,
                'previous_reviewer_id': last_line.previous_reviewer_id.id,
                'date': fields.Datetime.now()
            })
            review._send_review_notifications()
    
        if review.assignment_type == 'external':
            review.project_id.is_external_report_submitted = False

