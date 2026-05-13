# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ScheduleOfComplaintsDisplayWizard(models.TransientModel):
    _name = 'schedule.of.complaints.display'
    _description = 'Schedule Of Complaints Display Wizard'


    parent_case_id = fields.Many2one('crm.lead', 'Internal Case Title')
    case_ref_number = fields.Char(string='Ref.')
    allegation_source_id = fields.Many2one(related="parent_case_id.allegation_source_id", string='Source If Any')
    internal_coms_ref = fields.Char(related="parent_case_id.internal_coms_ref", string='Reference if Any')
    create_date = fields.Date(string="Date Reported to Forensic Services")
    allegation_nature_id = fields.Many2one(related="parent_case_id.allegation_nature_id", string="Nature of Complaints")
    allegation_description = fields.Html(related="parent_case_id.allegation_description", string='Brief Description of Matter(As Reported)')
    name = fields.Char(related="parent_case_id.name", string="Subjects")
    directorate_id = fields.Many2one(related="parent_case_id.directorate_id", string='Directorate')
    department_id = fields.Many2one(related="parent_case_id.department_id", string='Department')
    assignment_type_id = fields.Many2one('forensic.assignment.type', string="Assignment Type")
    review_note = fields.Text(related="parent_case_id.review_note", string='Comment')

    def download_schedule_of_complaints(self):
        return self.env.ref(
            'in2it_forensic_services.action_report_forensic_case_assignment_pdf'
        ).report_action(self.env.context.get('active_id'))


