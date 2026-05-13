# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################


from odoo import http
from odoo.http import request
from odoo.addons.sign.controllers.main import Sign
from ..models import crm_lead_forensic
from ..models.case_assignment import send_system_notification




class SignControllerOverride(Sign):

    @http.route(['/sign/sign_request_items'], type='json', auth='user')
    def get_sign_request_items(self, request_id, token):
        result = super().get_sign_request_items(request_id, token)
        sign_request = request.env['sign.request'].sudo().browse(request_id)
        if isinstance(result, list):
            return [{'case_ref_number':sign_request.authorization_template_id.case_ref_number,
                     'evidence':sign_request.evidence_template_id}]

        return result


    @http.route()
    def sign(self, sign_request_id, token, sms_token=False, signature=None, **kwargs):
        result = super().sign(sign_request_id, token, sms_token=sms_token, signature=signature, **kwargs)
        sign_request = request.env['sign.request'].sudo().browse(sign_request_id)

        if (
            sign_request
            and sign_request.exists()
            and sign_request.authorization_template_id
            and sign_request.state == 'signed'
        ):
            record = sign_request.authorization_template_id

            attachment = request.env['ir.attachment'].sudo().create({
                'name': sign_request.reference,
                'type': 'binary',
                'datas': sign_request.completed_document,
                'res_model': record._name,
                'res_id': record.id,
                'res_field':"signed",
                'mimetype': 'application/pdf',
            })

            record.sudo().message_post(
                body="✅ Authorization letter has been signed successfully.",
                attachment_ids=[attachment.id],
            )
            record.is_unauthorized = True

            # Generate actual sequence and increase stage by one
            stages = sign_request.authorization_template_id.associated_stage_ids.sorted('sequence')
            current_stage = sign_request.authorization_template_id.stage_id

            if sign_request.authorization_template_id.assignment_type_id in [request.env.ref('in2it_forensic_services.assignment_type_spk_rec'), request.env.ref('in2it_forensic_services.assignment_type_rec')]:
                sign_request.authorization_template_id.stage_id = request.env.ref('in2it_forensic_services.case_type_stage_closed')
            # Move to next stage
            else:
                if current_stage in stages:
                    idx = stages.ids.index(current_stage.id)  # index of current stage in all stages
                    if idx + 1 < len(stages):
                        sign_request.authorization_template_id.stage_id = stages[idx + 1]

            assignment_type_obj = sign_request.authorization_template_id.assignment_type_id.sequence_id
            if assignment_type_obj:
                code_seq = assignment_type_obj.next_by_code(assignment_type_obj.code)  # EFS/FOR/001
                year = crm_lead_forensic.get_financial_year(request.env)  # 25-26
                case_ref = f"{code_seq}/{year}"  # EFS/FOR/001/25-26
                sign_request.authorization_template_id.case_ref_number = case_ref
                sign_request.authorization_template_id.button_visibility = 'download'

              
        
            line_case_type = request.env.ref('in2it_forensic_services.assignment_type_line_refferal')
            case_type = record.assignment_type_id
            
            if line_case_type == case_type:
                nodals = request.env['res.users'].search([('directorate_id','=',record.directorate_id.id)])

                email_to = ','.join(nodals.mapped('login'))
                ctx = {'email_to': email_to}
                mail_template = request.env.ref('in2it_forensic_services.email_template_case_allocation_notification_directorate').sudo()
                if mail_template:
                    mail_template.with_context(ctx).send_mail(record.id, force_send=True)

            mail_template = request.env.ref('in2it_forensic_services.email_template_case_type_authorized').sudo()
            if mail_template:
                mail_template.send_mail(record.id, force_send=True)

        groups = (
            request.env.ref('in2it_forensic_services.group_fcm_case_pfo_access') |
            request.env.ref('in2it_forensic_services.group_fcm_review_access') |
            request.env.ref('in2it_forensic_services.group_fcm_case_fo_access') |
            request.env.ref('in2it_forensic_services.group_fcm_case_sfo_access')
        ).sudo()

        users = groups.mapped('users')

        if result.get('success'):
            sign_request = request.env['sign.request'].sudo().browse(sign_request_id)
            
            if sign_request.state == 'signed' and sign_request.authorization_template_id:
                for user in users:
                    send_system_notification(
                        request.env,
                        message=f"Case - '{sign_request.authorization_template_id.case_ref_number}' has been authorised.",
                        model='forensic.case.assignment',
                        user_id=user.id,
                        res_id=sign_request.authorization_template_id.id
                    )

        return result