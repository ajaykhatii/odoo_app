
from odoo import api, fields, models
from base64 import b64encode
import json
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup
import re


class ModelMessagePopup(models.TransientModel):
    _name = 'popup.wizard'
    _description = "Wiard to show message"
    
    message = fields.Html(
        string="Message",
        readonly=True,
        sanitize=False,
    )

class ChangeRequestWizard(models.TransientModel):
    _name = "change.request.wizard"
    _description = "Change Request Wizard"


    assignment_type_ids = fields.Many2many(
        'forensic.assignment.type',
        string="Assignment Type",
        required=True,
    )
    comment = fields.Text(string="Comment", required=True)

    def action_change_request(self):
        links_html = ""        
        action_id = 'in2it_forensic_services.action_forensic_case_authorization'
        form_id = 'in2it_forensic_services.view_forensic_case_assignment_form'
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') 
        forensic_case_assignment = self.env['forensic.case.assignment']
        old_forensic_case_assignment = forensic_case_assignment.browse(self.env.context.get('case_auth_id'))
        
        for rec in self:
            assignment_type = forensic_case_assignment.search([('id','=', self.env.context.get('case_auth_id')),('stage_id', '!=', old_forensic_case_assignment.assignment_type_id.stage_ids.ids[0])])
            if assignment_type:
                raise ValidationError(f"Case assignment stage should not be {assignment_type.stage_id.name}.")      

            if not rec.assignment_type_ids:
                raise ValidationError("Assignment type is required.")
            
            if not rec.comment:
                raise ValidationError('Comment input is required.')
            existing_assignment_type = old_forensic_case_assignment.parent_case_id.case_assignment_ids.mapped('assignment_type_id')
            common_ids = (self.assignment_type_ids & existing_assignment_type)
            if common_ids:
                raise ValidationError(
                    f"Assignment type already exists: {', '.join(map(str, common_ids.mapped('name')))}"
                )
            
            for type in rec.assignment_type_ids:
                sorted_stages = type.stage_ids.sorted(key=lambda l: (l.sequence, l.id))

                assignment_auth_vals = {
                    'assignment_type_id': type.id,
                    'comment':rec.comment,
                    'parent_case_id':old_forensic_case_assignment.parent_case_id.id,
                    'parent_case_ref':old_forensic_case_assignment.parent_case_id.internal_coms_ref,
                    'stage_id': sorted_stages[0].id if sorted_stages else False,
                    'associated_stage_ids': [(6, 0, sorted_stages.ids)],
                    'case_ref_number': old_forensic_case_assignment.parent_case_id.internal_coms_ref + '/' + type.name.upper()[:3], #EFS/COM/017/25-26/LIN
                    'is_new_request':True
                }
                new_forensic_case_assignment = forensic_case_assignment.create(assignment_auth_vals)
                # to show dynamic link for form view
                case_asgn = forensic_case_assignment.search([('id','=',new_forensic_case_assignment.id)])
                base_url += f'/web#id={new_forensic_case_assignment.id}&action={action_id}&view_type=form&model={self._name}&view_id={form_id}'
                links_html += f"""
                            <p>
                                <a href="{base_url}" target="_blank">
                                    👉 {case_asgn.case_ref_number}
                                </a>
                            </p>
                        """
                # Signature Logic
                case = new_forensic_case_assignment

                case_ref = f"{case.parent_case_ref}/{case.assignment_type_id.name}"

                old = old_forensic_case_assignment
                new = new_forensic_case_assignment

                # Build exact strings
                old_ref = f"{old.parent_case_ref}/{old.assignment_type_id.name}"
                new_ref = f"{old.parent_case_ref}/{new.assignment_type_id.name}"

                html = old.auth_html_content or ""

                # Exact string replacement
                html = html.replace(old_ref, new_ref)

                # Save back to new record
                new.auth_html_content = html

                department = self.env['hr.department'].search([('parent_id', '=', False)], limit=1)
                chief = department.manager_id.name
                assignment_type = case.assignment_type_id

                if assignment_type.id == self.env.ref('in2it_forensic_services.assignment_type_preliminary').id:
                    signer_position = "Chief of Ethics"
                    signer_name = chief
                else:
                    signer_position = "City Manager"
                    # group = self.env.ref('in2it_forensic_services.group_fcm_city_manager')
                    # user_in_group = self.env['res.users'].search([('groups_id', 'in', [group.id])],limit=1)
                    signer_name = self.env.user.name if self.env.user else ""

                pdf_content, _ = self.env['ir.actions.report'].with_context(
                    name=self.env.user.name,
                    email=self.env.user.email,
                    phone=self.env.user.phone,
                    mobile=self.env.user.mobile,
                    job_position=self.env.user.employee_id.job_id.name,
                    department_name=self.env.user.employee_id.department_id.name,
                    force_report_rendering=True,
                    show_case_details=True,
                    signature_url=(f"/web/image/res.users/{department.manager_id.user_id.id}/sign_signature"),
                    chief=chief,
                    signer_position=signer_position,
                    signer_name=signer_name,
                    case_type=type.name,
                    subject=old.auth_subject,
                )._render_qweb_pdf(
                    'in2it_forensic_services.case_auth_pdf_report',
                    [new_forensic_case_assignment.id],
                )

                generated_attachment = self.env['ir.attachment'].create({
                    'name': f'authorization_letter_{new_forensic_case_assignment.id}.pdf',
                    'type': 'binary',
                    'datas': b64encode(pdf_content),
                    'res_model': 'forensic.case.assignment',
                    'res_id': json.loads(
                        str(new_forensic_case_assignment.id)) if new_forensic_case_assignment else False,
                    'mimetype': 'application/pdf',
                })

                all_attachments = [generated_attachment.id]
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
                        'alignment': 'left'
                    })],
                })
                partner = self.env.user.partner_id.id
                # case.sign_request_ids.unlink()
                sign_request = self.env['sign.request'].create({
                    'authorization_template_id': case.id,
                    'template_id': template.id,
                    'reference': f'authorization_letter_{self.id}.pdf',
                    'request_item_ids': [(0, 0, {
                        'partner_id': partner,
                        'role_id': self.env.ref('sign.sign_item_role_customer').id,
                    })],
                })

                template = self.env.ref("in2it_forensic_services.case_auth_mail_template").sudo()
                record_id = json.loads(str(new_forensic_case_assignment.id))
                email_values = {
                    'email_to': ",".join(self.env.user.email),
                    'attachment_ids': [(6, 0, all_attachments)]
                }  
                ctx = {
                    'subject': old.auth_subject
                }
                template.with_context(ctx).send_mail(
                    record_id,
                    force_send=True,
                    email_values=email_values
                )
                case.write({'button_visibility': 'sign_auth'})

            # ------------------------------


            if self.env.context.get('case_auth_id'):
                old_forensic_case_assignment.comment = rec.comment
                old_forensic_case_assignment.assignment_type_ids = [(4,type.id) for type in rec.assignment_type_ids]
                old_forensic_case_assignment.stage_id = self.env.ref('in2it_forensic_services.case_type_stage_closed')
                old_forensic_case_assignment.record_link = links_html
                old_forensic_case_assignment.is_unauthorized = True

        return {
                'name': 'Submission Successful',
                'type': 'ir.actions.act_window',
                'res_model': 'popup.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('in2it_forensic_services.popup_wizard_form_view').id,
                'target': 'new',
                'context': {'default_message': links_html}
            }



        
