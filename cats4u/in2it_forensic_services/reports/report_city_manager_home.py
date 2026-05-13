# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import api, models

class ForensicCaseAssignment(models.AbstractModel):
    _name = 'report.in2it_forensic_services.report_forensic_case_assignment_pdf'
    _description = 'City Manager Home PDF Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env['forensic.case.assignment'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'forensic.case.assignment',
            'docs': records
        }
