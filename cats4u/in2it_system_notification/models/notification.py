from odoo import models,fields, api, _

class SystemNotification(models.Model):
    _name = "system.notification"
    _description = "This is a System Notification"
    _order = "create_date desc"
    _rec_name = "name"

    name = fields.Char("Notification Reference", required=True, copy=False, default="Draft")
    message = fields.Text()
    user_id = fields.Many2one("res.users", string="Assigned User (TO)" ,required=True)
    state = fields.Selection([
        ("unread", "Unread"),
        ("read", "Read")
    ], default="unread")
    res_model = fields.Char("Res Model related",related="res_model_id.model")
    res_id = fields.Integer("Res Id")
    res_model_id = fields.Many2one("ir.model", string="Res Model")
    partner_id = fields.Many2one("res.partner", string="Partner", default=lambda self: self.env.user.partner_id)



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Draft') == 'Draft':
                vals['name'] = self.env['ir.sequence'].next_by_code('system.notification.sequence') or 'Draft'
        
        # Create all records at once
        records = super(SystemNotification, self).create(vals_list)

        # Trigger real-time notifications
        for record in records:
            record.send_realtime_notification()

        return records
    
    def send_realtime_notification(self):
        self.env["bus.bus"]._sendone(
            self.user_id.partner_id,  
            "system_notification_channel",
            {
                "id": self.id,
                "message": self.message,
                "res_model": self.res_model or "", 
                "res_id": self.res_id or False,
                "state": self.state,
                "partner_id": self.partner_id.id,
            }
        )

        