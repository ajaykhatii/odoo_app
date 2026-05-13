# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RequestDigitalWizard(models.TransientModel):
    _name = "request.digital.wizard"
    _description = "Reuqest Digital Wizard"

    project_id = fields.Many2one("project.project", required=True)
    date_from = fields.Date("Date Start")
    date_to = fields.Date("Date To")
    comment = fields.Text("Comment")
    evidence = fields.Text("Evidence")
    suspect_ids = fields.Many2many('forensic.case.suspects', string="Suspects")

    @api.onchange('date_from','date_to')
    def _onchange_date(self):
        if self.date_from and self.date_to:
            if self.date_from > self.date_to:
                raise ValidationError("Date from can not be less than date to.")

    def action_confirm(self):
        city_manager = self.env['res.users'].search([('groups_id','=',self.env.ref('in2it_forensic_services.group_fcm_city_manager').id)])
        chief_digital_officer = self.env['res.users'].search([('position', '=', 'cdo')])
        return {
            'name': 'Request for Digital Access',
            'type': 'ir.actions.act_window',
            'res_model': 'request.access.digital.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'project_id': self.project_id.id,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'comment': self.comment,
                'suspect_ids': self.suspect_ids.ids,
                'evidence': self.evidence,
                'cm_users': city_manager.ids if city_manager else [],
                'cdo_users': chief_digital_officer.ids if chief_digital_officer else [],
                
                'default_cm_subject': "REQUEST FOR THE AUTHORISATION OF EMAIL COLLECTION AND SEARCH CRITERIA TO BE USED IN RESPECT OF FS304/24-25: ALLEGED UIFW EXPENDITURE AND MISMANAGEMENT OF FUNDS",
                'default_subject': "REQUEST FOR THE AUTHORISATION OF EMAIL COLLECTION AND SEARCH CRITERIA TO BE USED IN RESPECT OF XXXX",
            }
        }
