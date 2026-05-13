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
from odoo.exceptions import UserError, ValidationError
from ...in2it_forensic_services.controllers.sign_request_items import SignControllerOverride
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification




def get_financial_year(env, company_id=None):
    """
    Return financial year in 'YY-YY' format based on company settings.
    Example: '25-26'
    """
    # Get company (current user’s company if not passed)
    company = env['res.company'].browse(company_id) if company_id else env.company

    # Ensure FY dates are configured
    if not company.fy_start_date or not company.fy_end_date:
        raise ValidationError("Financial Year dates are not configured in the Company settings.")

    fy_start_year = company.fy_start_date.year
    fy_end_year = company.fy_end_date.year

    return f"{fy_start_year % 100:02d}-{fy_end_year % 100:02d}"


class SignControllerOverrideProject(SignControllerOverride):

    @http.route()
    def sign(self, sign_request_id, token, sms_token=False, signature=None, **kwargs):
        result = super().sign(sign_request_id, token, sms_token=sms_token, signature=signature, **kwargs)
        sign_request = request.env['sign.request'].sudo().browse(sign_request_id)
        assignment_type_obj = sign_request.authorization_template_id.assignment_type_id.sequence_id

        if sign_request and sign_request.evidence_template_id:
            evidence = sign_request.evidence_template_id
            
            if evidence.digital_access == 'cdo':
                evidence.sudo().write({'status': 'approved'})
                for lead_investigator in evidence.lead_investigator_ids:
                    message=f"Your Digital Access Request for Case: { evidence.project_id.name } has been approved.You may now proceed with Digital Evidence Collection activities."
                    model=sign_request.evidence_template_id._name,
                    user_id=lead_investigator.id,
                    res_id=sign_request.evidence_template_id.id
                    if user_id and res_id and model:
                        send_system_notification(request.env,message,model,user_id,res_id)

            elif evidence.digital_access == 'city_manager':
                email_values = {
                        'attachment_ids': [(6, 0, sign_request.evidence_template_id.attachment_ids.ids)],
                        'email_to': sign_request.template_id.user_id.login,
                    }
                base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                base_url += '/my/home'
                
                template = request.env.ref("in2it_project_management.mail_template_case_request_digital_access_Chief_digital_officer")
                if template:
                    template.with_context({'subject': sign_request.template_id.subject,'url': base_url}).send_mail(evidence.id, email_values=email_values,force_send=True)
                    evidence.sudo().write({'digital_access': 'cdo'})

        if sign_request and sign_request.overarching_memo_template_id:
            memo = sign_request.overarching_memo_template_id
            if memo.memo_pending_at == 'city_manager':
                recommendation = memo.project_id.recom_project_ids.filtered(lambda l: not l.for_efs)
                if not recommendation:
                    memo.sudo().write({'status': 'approved', 'memo_pending_at': 'none'})
                    for lead_investigator in memo.lead_investigator_ids:
                        message = f"The overarching memo has been approved."
                        model = memo._name
                        user_id = lead_investigator.id
                        res_id = memo.id
                        if user_id and res_id and model:
                            send_system_notification(request.env, message, model, user_id, res_id)
                else:
                    email_to = ','.join(memo.distribution_line_ids.mapped('user_id.employee_id.work_email'))
                    base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    base_url += '/my/home'
                    
                    email_values = {'email_to': email_to}
                    template = request.env.ref("in2it_project_management.mail_template_case_overarching_memo_approved_excutive_directorate")
                    if template:
                        memo.memo_pending_at = 'ed'
                        template.with_context({'url':base_url}).send_mail(memo.id, email_values=email_values, force_send=True)
                        

        if assignment_type_obj:
            case_type = request.env['forensic.assignment.type'].search([('id','=',sign_request.authorization_template_id.assignment_type_id.id),('is_project_create','=',True)])
            if case_type:
                project_vals = {
                    'name':sign_request.authorization_template_id.case_ref_number,
                    'user_id' : sign_request.authorization_template_id.investigation_manager_id.user_id.id,
                    'case_id' : sign_request.authorization_template_id.parent_case_id.id,
                    'assignment_id' : sign_request.authorization_template_id.id,
                    'partner_id' : sign_request.authorization_template_id.parent_case_id.partner_id.id,
                    'company_id':sign_request.authorization_template_id.parent_case_id.partner_id.company_id.id,
                    'description' : sign_request.authorization_template_id.parent_case_id.allegation_description,
                    'physical_item_ids': [
                            (0, 0, {
                                'item_title': item.item_title,
                                'item_category': item.item_category,
                                'quantity': item.quantity,
                                'uom_id': item.uom_id.id if item.uom_id else False,
                                'source': item.source,
                                'recovery_location': item.recovery_location,
                                'associated_with': item.associated_with,
                                'storage_location': item.storage_location,
                                'current_custodian': item.current_custodian.id if item.current_custodian else False,
                                'status': item.status,
                                'last_movement_date': item.last_movement_date,
                                'is_from_case':True
                            })
                            for item in sign_request.authorization_template_id.parent_case_id.physical_item_ids
                        ],

                    'suspect_ids': [
                        (0, 0, {
                            'name': s.name,
                            'company_name': s.company_name,
                            'email': s.email,
                            'phone': s.phone,
                            'type': s.type,
                            'vendor_emp': s.vendor_emp,
                        })
                        for s in sign_request.authorization_template_id.parent_case_id.suspect_ids
                    ],

                    'document_line_ids': [
                        (0, 0, {
                            'description': s.description,
                            'document_type_id': s.document_type_id.id if s.document_type_id else False,
                            'document_stores': s.document_stores,
                            'document_stores_location': s.document_stores_location,
                            'uploaded_by':s.uploaded_by.id or False,
                            'file':s.file,
                            'file_name':s.file_name,
                            'is_from_case':True
                        })
                        for s in sign_request.authorization_template_id.parent_case_id.document_line_ids
                    ],
                    'witness_ids': [
                        (0, 0, {
                            'name': s.name,
                            'phone': s.phone,
                            'email': s.email,
                        })
                        for s in sign_request.authorization_template_id.parent_case_id.witness_ids
                    ],
                    'investigation_directorates_ids': [
                        (0, 0, {
                            'directorate_id': sign_request.authorization_template_id.directorate_id.id,
                            'department_id': sign_request.authorization_template_id.department_id.id,
                        })
                    ],
                    }
                
                timesheet_module = request.env['ir.module.module'].sudo().search(
                    [('name', '=', 'hr_timesheet'), ('state', '=', 'installed')],
                    limit=1
                )
                if timesheet_module:
                    project_vals['allow_timesheets'] = True
                project = request.env['project.project'].sudo().create(project_vals)
       

        return result