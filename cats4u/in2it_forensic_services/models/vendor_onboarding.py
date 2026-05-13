from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VendorOnboarding(models.Model):
    _inherit = "res.partner"
    

    spoc_name = fields.Char(string="SPOC Name",tracking=True)
    vendor_status = fields.Selection([('active','Active'),('inactive','Inactive')],default='active',string="Vendor Status",tracking=True)
    is_vendor = fields.Boolean(string='Vendor',tracking=True)



    @api.constrains('name')
    def check_vendor_name(self):
        for rec in self:
            if rec.name and rec.is_vendor:
                duplicate_vendor = self.env['res.partner'].search([
                    ('name', '=ilike', rec.name),
                    ('is_vendor','=',True),
                    ('id', '!=', rec.id)  # Exclude the current record
                ],limit=1)
                if duplicate_vendor:
                    raise ValidationError(
                        f"A vendor with the name {rec.name} already exists.")
                