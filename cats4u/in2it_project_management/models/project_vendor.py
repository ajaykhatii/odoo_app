# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _
import secrets
from datetime import timedelta
from odoo.exceptions import ValidationError
from odoo.tools import single_email_re


class InvestigationVendorLine(models.Model):
    _name = 'investigation.vendor.line'
    _description = 'Investigation Vendor Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'partner_id'
    _order = "id desc"

    partner_id = fields.Many2one('res.partner', string="Vendor", tracking=True)
    project_id = fields.Many2one('project.project', string="Project", tracking=True)
    token = fields.Char(string="Token")
    status = fields.Selection([
        ('new', 'New'), 
        ('pending', 'Pending'),
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('expire', 'Token Expire')],
        string="Status", default="new")
    email = fields.Char(string="Email", related="partner_id.email")
    phone = fields.Char(string="Phone", related="partner_id.phone")
    mobile = fields.Char(string="Mobile", related="partner_id.mobile")
    expiration_date = fields.Datetime(string="Link Expiration", readonly=True, tracking=True)
    action_date = fields.Datetime(string="Action Date", readonly=True, tracking=True)
    token_duration = fields.Integer(
        string="Token Duration (in seconds)",
        compute="_compute_token_duration"
    )

    @api.depends('expiration_date', 'status')
    def _compute_token_duration(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.status == 'pending' and rec.expiration_date:
                delta = rec.expiration_date - now
                rec.token_duration = max(int(delta.total_seconds()), 0)

                if rec.token_duration == 0:
                    rec.status = 'expire'
            else:
                rec.token_duration = 0

    # Send Web Link
    def action_send_weblink_to_vendor(self):
        token_expire_hours = self.env['ir.config_parameter'].sudo().get_param('in2it_vendor.token_expire_duration', default=48)  # make config from setting
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        for rec in self:
            project_vendor = self.search([('project_id','=',rec.project_id.id),('status','in',['pending', 'accept'])])
            if project_vendor:
                raise ValidationError("You have already have a 'Pending/Accepted' Vendor. You can not create new vendor")


            if self.email and not single_email_re.match(self.email):
                raise ValidationError("Primary email not correct.")
            
            token = secrets.token_urlsafe(32)
            token_expiration = fields.datetime.now() + timedelta(hours=int(token_expire_hours))
            rec.write({
                'expiration_date':token_expiration,
                'token':token,
                'status':'pending',
            })

            url = f"{base_url}/vendor/tor/{rec.project_id.id}/{token}"
            template = self.env.ref(
                'in2it_project_management.mail_template_line_terms_of_refrence',
                raise_if_not_found=False
            )
            
            if template:
                template.with_context(
                    project=rec.project_id.id,
                    partner_name=rec.partner_id.name,
                    token_expire_hours=token_expire_hours,
                    url=url,
                    ).send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'email_to': rec.email},
                )

    def unlink(self):
        for record in self:
            if record.status != 'new':
                raise ValidationError("You can only delete records in 'New' state.")
        return super().unlink()

