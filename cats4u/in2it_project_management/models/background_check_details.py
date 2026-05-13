# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BackgroundCheck(models.Model):
    _name = 'background.check.details'
    _description = 'Background Check'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'subject_name'

    project_id = fields.Many2one('project.project', string="Project")
    subject_type = fields.Selection([
        ('individual', 'Individual'),
        ('entity', 'Entity'),
        ('organization', 'Organization')
    ], string="Subject Type", required=True, tracking=True)

    subject_name = fields.Char(
        string="Subject Name",
        required=True,
        size=200,
        tracking=True
    )

    date_from = fields.Date(
        string="Date From",
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    date_to = fields.Date(
        string="Date To",
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    investigator_id = fields.Many2one(
        'res.users',
        string="Investigator",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        readonly=True,
    )

    status = fields.Selection([
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string="Status", required=True, default='in_progress', tracking=True)

    # Validation: To date cannot be before From date
    @api.onchange('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_to < record.date_from:
                    raise ValidationError(
                        "Date Performed To cannot be before Date Performed From."
                    )

    database_id = fields.Many2one('background.database', string="Databases")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records:
            if record.project_id:
                record._notify_project_on_creation()

        return records
    
    def _notify_project_on_creation(self):
        self.ensure_one()

        body = _(
            """New Background Check Added
                Project: %s
                Subject: %s
                Performed From: %s
                Performed To: %s
                Created By: %s
                """
                    ) % (
            self.project_id.display_name,
            self.display_name,
            self.date_from or '',
            self.date_to or '',
            self.create_uid.name,
        )

        # Post on PROJECT chatter
        self.project_id.message_post(
            body=body,
            message_type="notification",
            subtype_xmlid="mail.mt_comment",
        )

    description = fields.Text(string="Description")
    is_other = fields.Boolean(string="Other")
    remark = fields.Text(string="Remarks")
    attachment_ids = fields.Many2many('ir.attachment', 'backgorund_attachment_rel', 'project_id' , "background_attachment_id", string="Attachment", tracking=True)


    @api.onchange('database_id')
    def action_description(self):
        for rec in self:
            rec.is_other = False
            if rec.database_id == self.env.ref('in2it_project_management.database_other_records'):
                rec.is_other = True


    def action_submit(self):
        return {
            'name': _('Action Submit'),
            'type': 'ir.actions.act_window',
            'res_model': 'remark.wizard',
            'view_mode': 'form',
            'target': 'new',  # important for popup
            'context': {
                'default_background_check_id': self.id,
                'status': 'submit',
            }
        }
    
    def action_cancel(self):
        return {
            'name' : _('Action Cancel'),
            'type' : 'ir.actions.act_window',
            'res_model' : 'remark.wizard',
            'view_mode' : 'form',
            'target' : 'new',
            'context' : {
                'default_background_check_id' : self.id,
                'status' : 'cancel'
            }

        }

class BackgroundDatabases(models.Model):
    _name = 'background.database'
    _description = 'Background Checks Databases'

    name = fields.Char(string="Name")