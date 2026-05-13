from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ForensicCloseCaseWizard(models.TransientModel):
    _name = 'forensic.case.close.wizard'
    _description = 'Close Case Confirmation Wizard'

    case_id = fields.Many2one('forensic.case.assignment', required=True)
    response = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Response", required=True)

    comment = fields.Text(string="Comment")

    def action_confirm(self):
        self.ensure_one()

        close_stage = self.env.ref(
            'in2it_forensic_services.case_type_stage_closed',
            raise_if_not_found=False
        )

        if close_stage:
            self.case_id.sudo().write({
                'stage_id': close_stage.id,
                'assignment_stage': 'closed',
                'closure_response': self.response,
                'closure_comment': self.comment,
            })