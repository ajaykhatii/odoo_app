from odoo import models, fields
from odoo.exceptions import ValidationError

class AssignVendorWizard(models.Model):
    _name = 'assign.vendor.wizard'
    _description = 'Assign Vendor Wizard'

    project_id = fields.Many2one('project.project', string="Project")
    partner_id = fields.Many2one('res.partner', string="Vendor")
    
    def action_add_vendor(self):
        for rec in self:
            if rec.project_id and rec.partner_id:
                if not rec.partner_id.email:
                    raise ValidationError(f"Email should be present in vendor - {rec.partner_id.name}")
                
                partner_vals = {
                    'partner_id': rec.partner_id.id,
                    'project_id':rec.project_id.id
                }
                new_lines = self.env['investigation.vendor.line'].create(partner_vals)
                if self.env.context.get('another_vendor'):
                    for line in new_lines:
                        line.action_send_weblink_to_vendor()