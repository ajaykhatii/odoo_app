from odoo import models,_
from odoo.exceptions import UserError


class IrModuleModuleInherit(models.Model):
    _inherit = 'ir.module.module'

    def button_immediate_install(self):
        for module in self:
            if not module.name.lower().startswith('in2it'.lower()):
                raise UserError("You cannot install this app. Please contact your Administrator.")
        return super().button_immediate_install()
    
    
    def _block_in2it_uninstall(self):
        for module in self:
            if module.name and module.name.lower().startswith('in2it'.lower()):
                raise UserError(
                    _("Once an app is installed you cannot uninstall it. Please contact your Administrator."))
            

    def button_uninstall_wizard(self):
        self._block_in2it_uninstall()
        return super().button_uninstall_wizard()
    