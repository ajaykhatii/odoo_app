from odoo import fields, models, api, _


class CmsReportConfig(models.Model):
    _name = 'cms.report.config'
    _description = 'CMS Report Config'

    name = fields.Char(string="Name")
    group_ids = fields.Many2many('res.groups', string="Groups")
    active = fields.Boolean(default=True)
