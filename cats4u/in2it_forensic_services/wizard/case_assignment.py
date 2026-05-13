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


class CaseAssignmentWizard(models.TransientModel):
    """Temporary model to assign a COM case to a specific type"""
    _name = 'case.assignment.transient'
    _description = 'Case Assignment Wizard'

    case_id = fields.Many2one('crm.lead', 'Case')
    assignment_type_ids = fields.Many2many('forensic.assignment.type',
                                       string="Case Type")
    note = fields.Text('Comment')


    
    def action_case_assign(self):
        """Create forensic.case.assignment only if not already exists for this lead and when assignment type is set.
            #     with COM reference and Case type as draft eg. EFS/COM/017/25-25/LIN"""
        self.ensure_one()
        Assignment = self.env['forensic.case.assignment'].sudo()
        for assign_type in self.assignment_type_ids:
            # Check if assignment already exists for this (lead + type)
            existing = Assignment.search([
                ('parent_case_id', '=', self.case_id.id),
                ('assignment_type_id', '=', assign_type.id),
            ], limit=1)

            if existing:
                continue  # skip duplicates

            # Fetch type-specific ordered stages
            sorted_stages = assign_type.stage_ids.sorted(
                key=lambda l: (l.sequence, l.id)
            )
            # Create assignment
            document_lines_vals = []
            evidence_lines_vals = []

            # if case 
            if assign_type.name == "LIN":
                for doc in self.case_id.document_line_ids:
                    document_lines_vals.append((0, 0, {
                        'file': doc.file,
                        'file_name':doc.file_name,
                        'description': doc.description,
                        'uploaded_by':doc.uploaded_by.id if doc.uploaded_by else False,
                        'uploaded_date':doc.uploaded_date,
                        'document_type_id':doc.document_type_id.id if doc.document_type_id else False,
                        'document_stores':doc.document_stores,
                        'document_stores_location':doc.document_stores_location,
                        'is_from_case':True
                    }))
                for doc in self.case_id.physical_item_ids:
                    evidence_lines_vals.append((0, 0, {
                        'item_title': doc.item_title,
                        'item_category':doc.item_category,
                        'quantity': doc.quantity,
                        'uom_id':doc.uom_id.id if doc.uom_id else False,
                        'source':doc.source,
                        'current_custodian':doc.current_custodian.id if doc.current_custodian else False,
                        'status':doc.status,
                        'associated_with':doc.associated_with,
                        'attachment_ids':[[6,0,[rec.id for rec in doc.attachment_ids]]],
                        'is_from_case':True
                    }))

            Assignment.create({
                'parent_case_id': self.case_id.id,
                'assignment_type_id': assign_type.id,
                'associated_stage_ids': [(6, 0, sorted_stages.ids)],
                'stage_id': sorted_stages[0].id if sorted_stages else False,
                'case_ref_number': self.case_id.internal_coms_ref + '/' + assign_type.name.upper()[:3],
                'document_line_ids': document_lines_vals,
                'physical_item_ids':evidence_lines_vals

                # EFS/COM/017/25-26/LIN
            })

        case_types = set(self.case_id.assignment_type_ids.ids)
        assigned_types = set(self.case_id.case_assignment_ids.mapped('assignment_type_id').ids)
        remaining_case_types = list(case_types - assigned_types)

        if not remaining_case_types:
            activity_id = self.case_id.activity_ids.filtered(
                lambda a: a.summary == 'Request Classification'
            )[:1]
            if activity_id:
                activity_id.action_done()

        self.case_id.message_post(
            body=self.note or (
                f"Case Assigned : {', '.join(self.assignment_type_ids.mapped('name'))}"
                if self.assignment_type_ids else "Case Assigned"
            ),
            message_type="comment"
            )

    def action_case_close(self):
        self.ensure_one()
        self.case_id.active = False
        self.case_id.review_note = self.note


    def action_send_classification_request(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        case = self.env[active_model].browse(active_id)
        activity_values = {
            "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
            "res_id": active_id,
            "res_model_id": self.env['ir.model']._get_id("crm.lead"),
            "user_id": case.create_uid.id,
            "summary": "Request Classification",
            "note": self.note,
        }

        self.env["mail.activity"].with_context(
            mail_create_nosubscribe=True,
            mail_activity_quick_update=True
        ).create(activity_values)
        
        case.write({
            'classification_done': True,
            'review_note': self.note,
            'assignment_type_ids': [(6, 0, self.assignment_type_ids.ids)],
        })
        return {'type': 'ir.actions.act_window_close'}