# -*- coding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import fields, models, api, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    token_expire_duration = fields.Integer(
        string="Token Expire Duration (in hours)",
        config_parameter='in2it_vendor.token_expire_duration',
        default=48,
        help="Specify how long (in hours) the vendor token link should remain valid. Default is 48 hours."
    )
