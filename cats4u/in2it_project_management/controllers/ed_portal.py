from odoo import http
from odoo.http import request
import base64
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification

class PortalLiveSignature(http.Controller):

    @http.route(['/my/memos'], type='http', auth="user", website=True)
    def portal_memo(self, **kwargs):
        memos = request.env['overarching.memo'].sudo().sudo().search([('status','=','pending'),('memo_pending_at','=','ed')])

        return request.render(
            'in2it_project_management.portal_live_signature_page',
            {
                'memos': memos,
                'page_name':'memos'
            }
        )
    
    @http.route('/my/memo/<int:memo_id>', type='http', auth='user', website=True)
    def portal_overarching_memo(self, memo_id):
        memo = request.env['overarching.memo'].sudo().browse(memo_id)
        if memo.exists():
            project = memo.project_id
            sign_request = request.env['sign.request'].sudo().search([
                ('overarching_memo_template_id', '=', memo.id)
            ])

            annexure_docs = request.env['forensic.document.line'].sudo().search([
                ('is_annexure', '=', True),
                ('project_id', '=', project.id)
            ])
            
            exhibit_docs = request.env['complaint.physical.item'].sudo().search([
                ('is_exhibit', '=', True),
                ('project_id', '=', project.id)
            ]).mapped('attachment_ids')

            return request.render('in2it_project_management.ed_navar_page', {
                'memo': memo,
                'page_name':'memo',
                'investigation': project,
                'annexure_docs': annexure_docs,
                'exhibit_docs': exhibit_docs,
                'sign_requests': sign_request,
                'active_tab': request.params.get('tab', 'document')
            })
    
    @http.route('/my/memo/report/<int:memo_id>', type='http', auth='user', website=True)
    def poratl_overarching_memo(self, memo_id):
        memo = request.env['overarching.memo'].sudo().browse(memo_id)
        if memo.exists():
            project = memo.project_id
            
            attachment = request.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'project.project'),
                ('res_id', '=', project.id),
                ('name', '=', f'Investigation_report {project.name}.pdf')
            ], limit=1)

            if not attachment:
                if memo.case_type == 'pre':
                    pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf('in2it_project_management.action_pre_investigation_report',[project.id])
                else:
                    pdf_content, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf('in2it_project_management.action_investigation_report',[project.id])
        
                attachment = request.env['ir.attachment'].sudo().create({
                    'name': f'Investigation_report { project.name }.pdf',
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'project.project',
                    'res_id': project.id,                     
                    'mimetype': 'application/pdf',
                })
            return request.render('in2it_project_management.ed_navar_page', {
                'memo': memo,
                'page_name':'memo',
                'investigation_report': [attachment],
                'active_tab': request.params.get('tab', 'document')
            })

    @http.route('/my/memo/acknowledge/<int:request_id>', type='http', auth='user', website=True)
    def acknowledge_document(self, request_id, **kwargs):
        sign_req = request.env['sign.request'].sudo().browse(request_id)

        if not sign_req.exists():
            return request.not_found()
        
        memo_id = sign_req.overarching_memo_template_id
        user = request.env.user

        for line in memo_id.distribution_line_ids:
            if line.user_id.id == user.id:
                line.sudo().write({'status': 'approved'})

        all_approved = all(line.status == 'approved' for line in memo_id.distribution_line_ids)
        if all_approved:
            memo_id.sudo().write({'status': 'approved'})

            message = f"The overarching memo has been approved by the ED."
            model = memo_id._name
            res_id = memo_id.id
            if memo_id.city_manager_id:          
                user_id = memo_id.city_manager_id.id
                if user_id and res_id and model:
                    send_system_notification(request.env, message, model, user_id, res_id)
            
            for lead in memo_id.lead_investigator_ids:
                user_id = lead.id
                if user_id and res_id and model:
                    send_system_notification(request.env, message, model, user_id, res_id)

        return request.render('in2it_project_management.thank_you_dialog', {
            'memo_id': memo_id.id
        })