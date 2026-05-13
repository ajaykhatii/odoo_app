
from odoo import api, fields, models
from base64 import b64encode
import json
from odoo.exceptions import ValidationError

class CaseMemoWizard(models.TransientModel):
    _name = "casetype.authorize.wizard"
    _description = "Case Memo Wizard"

    case_type_id = fields.Many2one("forensic.case.assignment")
    # recipient_name = fields.Char("Recipient Name", required=True)
    sender_name = fields.Char("Sender Name", default=lambda self: self.env.user.name)
    recipient_address = fields.Char("Recipient Address")
    auth_body = fields.Html("Authorization Body")
    model = fields.Char('Related Document Model')
    res_ids = fields.Text('Related Document IDs')
    attachment_ids = fields.Many2many(
        'ir.attachment', string="Attachments"
    )

    @api.constrains('attachment_ids')
    def _check_total_attachment_size(self):
        MAX_SIZE = 10 * 1024 * 1024  # 10 MB in bytes

        for rec in self:
            total_size = sum(rec.attachment_ids.mapped('file_size') or [0])

            if total_size > MAX_SIZE:
                rec.attachment_ids = False
                raise ValidationError(
                    "Total attachment size must not exceed 10 MB."
                )

    user_id = fields.Many2one(
            'res.users',
            string="To")

    subject = fields.Char(string="Subject", default="REQUEST FOR APPROVAL TO - ")


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # template = self.env.ref("in2it_forensic_services.line_auth_letter").sudo()
        case = self.env["forensic.case.assignment"].browse(self.env.context.get("active_id"))
        if case.exists():
            template = case.assignment_type_id.auth_template_id
        else:
            return res

        ctx = {
            "sender_name": self.env.user.name,
            "case_refrence":case.parent_case_ref,
            "line_refrence":case.case_ref_number,
        }
        # Render template with dynamic values
        if template:
            rendered = self.env["ir.qweb"]._render(template.id, ctx)
            res["auth_body"] = rendered

        active_model = self.env.context.get('active_model', 'forensic.case.assignment')
        res['model'] = active_model
        active_id = self.env.context.get('active_id')
        res['res_ids'] = json.dumps([active_id]) if active_id else '[]'        
        
        return res
  

    def action_send_mail(self):
        active_id = self.env.context.get('active_id')
        case = self.env["forensic.case.assignment"].browse(active_id)
        pre_type = self.env.ref("in2it_forensic_services.assignment_type_preliminary").sudo()
        if case:
            case.auth_html_content = self.auth_body
            case.auth_subject = self.subject
        user_attachment_ids = self.attachment_ids.ids if self.attachment_ids else []
        department = self.env['hr.department'].search([('parent_id','=',False)],limit=1)
        chief = department.manager_id.name if department and department.manager_id else False
        authority_position = case.assignment_type_id.authority_id.name or False
        signer_position = ""
        if authority_position:
            signer_position = authority_position
        signer_name = self.user_id.name if self.user_id else ""

        chief_sign_date = fields.Datetime.now()
        chief_user = department.manager_id.user_id if department and department.manager_id else False
        if case.assignment_type_id.id == pre_type.id:
            signature_data = False
        else:
            signature_data = chief_user.sudo().sign_signature if chief_user else ""
        pdf_content, _ = self.env['ir.actions.report'].with_context(
                name=self.env.user.name,
                email=self.env.user.email,
                phone=self.env.user.phone,
                mobile=self.env.user.mobile,
                job_position=self.env.user.employee_id.job_id.name,
                department_name=self.env.user.employee_id.department_id.name,
                force_report_rendering=True,
                show_case_details=True,
                signature_bin=signature_data,
                chief=chief,
                signer_position=signer_position,
                signer_name=signer_name,
                subject=self.subject,
                chief_sign_date=chief_sign_date
                )._render_qweb_pdf(
                'in2it_forensic_services.case_auth_pdf_report',
                [case.id],
            )
        
    
        generated_attachment = self.env['ir.attachment'].create({
            'name': f'authorization_letter_{self.id}.pdf',
            'type': 'binary',
            'datas': b64encode(pdf_content),
            'res_model': self.model,
            'res_id': json.loads(self.res_ids)[0] if self.res_ids else False,
            'mimetype': 'application/pdf',
        })

        # Collect user attachments
        user_attachment_ids = self.attachment_ids.ids if self.attachment_ids else []
        all_attachments = [generated_attachment.id] + user_attachment_ids
        template = self.env['sign.template'].create({
            'name': f'authorization_letter_{self.id}.pdf',
            'attachment_id': generated_attachment.id,
            'sign_item_ids': [(0, 0, {
                'type_id': self.env.ref('sign.sign_item_type_signature').id,
                'required': True,
                'responsible_id': self.env.ref('sign.sign_item_role_customer').id,                
                'page': 2,
                'posX': 0.248,
                'posY': 0.213,
                'width': 0.200,
                'height': 0.050,

            }),
            (0, 0, {
                'type_id': self.env.ref('in2it_forensic_services.sign_item_type_datetime').id,
                'required': True,
                'responsible_id': self.env.ref('sign.sign_item_role_customer').id,            
                'page': 2,
                'posX': 0.249,
                'posY': 0.273,
                'width': 0.200,
                'height': 0.015,

            }),
            (0, 0, {
                'type_id': self.env.ref('sign.sign_item_type_multiline_text').id,
                'required': True,
                'responsible_id': self.env.ref('sign.sign_item_role_customer').id,
                'page': 2,
                'posX': 0.100,
                'posY': 0.351,
                'width': 0.600,
                'height': 0.060,
                'alignment':'left'
            })],
        })
        partner = self.user_id.partner_id.id if self.user_id else False
        # case.sign_request_ids.unlink()
        sign_request = self.env['sign.request'].with_context(
                skip_sign_access_mail=True
            ).create({
                'authorization_template_id': active_id,
                'template_id': template.id,
                'reference': f'authorization_letter_{self.id}.pdf',
                'request_item_ids': [(0, 0, {
                    'partner_id': partner,
                    'role_id': self.env.ref('sign.sign_item_role_customer').id,
                })],
            })

        # Send email using template
        template = self.env.ref("in2it_forensic_services.case_auth_mail_template").sudo()
        record_id = json.loads(self.res_ids)[0]
        email_values = {
            'email_to': self.user_id.email,
            'attachment_ids': [(6, 0, all_attachments)]
        }
        # ctx = 
        template.with_context({
            'subject':self.subject,
            'mail_notify_force_send':False

        }).send_mail(
            record_id,
            email_values=email_values,
        )
        case.write({'button_visibility': 'sign_auth'})


class SignRequest(models.Model):
    _inherit = 'sign.request.item'

    def _send_signature_access_mail(self):
        if self.env.context.get('skip_sign_access_mail'):
            self.write({'is_mail_sent': True})
            return
        return super()._send_signature_access_mail()

