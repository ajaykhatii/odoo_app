# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

from odoo import models, fields, api, _

class InheritIrAttachment(models.Model):
    _inherit = "ir.attachment"

    public = fields.Boolean('Is public document',default=True)