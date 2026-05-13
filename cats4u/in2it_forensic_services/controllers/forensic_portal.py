import binascii
from odoo import http,_,fields
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.addons.portal.controllers.portal import CustomerPortal
from ..models.case_assignment import send_system_notification
import base64
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification

class ForensicPortal(CustomerPortal):

    def prepare_domain(self):
        assigned_to_directorate_stage = request.env.ref('in2it_forensic_services.case_type_stage_assigned_to_directorate',raise_if_not_found=False)
        case_type = request.env.ref('in2it_forensic_services.assignment_type_line_refferal',raise_if_not_found=False)
        assigned_to_directorate_stage_id = assigned_to_directorate_stage.id if assigned_to_directorate_stage else 0
        case_type_id = case_type.id if case_type else 0
        # directorate = request.env.user.directorate_id
        # directorate_id = directorate.id if directorate else 0 

        return [('stage_id','=',assigned_to_directorate_stage_id),('assignment_type_id','=',case_type_id)]

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        domain = self.prepare_domain()
        user = request.env.user
        if 'case_count' in counters:
            if user.position == 'ed' or user.position == "nodal":
                case_type = request.env['forensic.case.assignment']
                try:
                    count = case_type.search_count(domain)
                except AccessError:
                    count = 0
            else:
                count = 0
            values['case_count'] = count

        return values

    @http.route(['/my/authorise/case'], type='http', auth="user", website=True)
    def authorise_case(self, **kw):
        """Render the portal page for cases to authorize"""
        domain = self.prepare_domain()
        cases = request.env['forensic.case.assignment'].sudo().search(domain)
        values = self._prepare_portal_layout_values()

        if request.env.user.position == 'ed':
            action = request.env['ed.action.line'].sudo().search([
                ('user_id', '=', request.env.user.id),
                ('status', '!=', 'completed')
            ])
            recom_cases = action.mapped('recom_id').filtered(
                lambda r: r.status and not r.for_efs
            )
            project_ids = recom_cases.mapped('project_id')

        unique_projects = project_ids
        values.update({
            'cases': cases,
            'unique_projects':unique_projects,
            'page_name': 'case',
            'user': request.env.user,
            'recommendation_cases': recom_cases
        })
        return request.render('in2it_forensic_services.portal_my_authorise_cases', values)
    

    @http.route(['/submit/message/<string:msg>'], type='http', auth="user", website=True)
    def submit_message(self, msg, **kw):
        return request.render('in2it_forensic_services.portal_success_msg', {'msg':msg})
    

    @http.route(
        ['/my/recommendations/<int:recom_id>'],
        type='http',
        auth="user",
        website=True,
        methods=['GET', 'POST']
    )
    def portal_recommendation_page(self, recom_id, message=False, access_token=None, **kw):
        try:
            recommendation_sudo = self._document_check_access(
                'project.category',
                recom_id,
                access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'recommendation_sudo': recommendation_sudo,
            'message': message,
            'report_type': 'html',
        }
        
        # Chatter support in portal
        history_session_key = 'my_recommendation_history'
        values = self._get_page_view_values(
            recommendation_sudo,
            access_token,
            values,
            history_session_key,
            False
        )

        if request.httprequest.method == 'POST':
            action = kw.get('action')
            remark = kw.get('remarks')
            status = kw.get('status')
            files = request.httprequest.files.getlist('attachment_ids')

            if action == 'submit_feedback':
                if not status:
                    raise ValidationError("Status is required.")
                if not remark:
                    raise ValidationError("Remark is required.")
                if not files:
                    raise ValidationError("Please upload at least one file.")

                ed_action_line = recommendation_sudo.ed_action_line_ids.filtered(
                    lambda r: r.user_id.id == request.env.user.id and r.status == 'pending'
                )[:1]

                if ed_action_line:
                    update_vals = {
                        'status': status,
                        'action_date': fields.Datetime.now(),
                        'action_by' : request.env.user.id,
                        'remark': remark,
                    }

                    attachment_ids = []
                    for file in files:
                        attachment = request.env['ir.attachment'].sudo().create({
                            'name': file.filename,
                            'datas': base64.b64encode(file.read()),
                            'res_model': 'ed.action.line',
                            'res_id': ed_action_line.id,
                            'mimetype': file.mimetype,
                        })
                        attachment_ids.append(attachment.id)

                    if attachment_ids:
                        update_vals['attachment_ids'] = [(6, 0, attachment_ids)]

                    ed_action_line.write(update_vals)
                    msg = "Submission Successfully."
                    return request.redirect(f'/submit/message/{msg}')

        return request.render(
            'in2it_forensic_services.investigation_recommendation_form_view',
            values
        )


    @http.route(['/ed/projects/<int:project_id>'], type='http', auth="user", website=True, methods=['GET', 'POST'])
    def ed_case_investigations(self, project_id, message=False, access_token=None, **kw):
        try:
            project_sudo = self._document_check_access('project.project', project_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        if request.env.user.position == 'ed':
            action = request.env['ed.action.line'].sudo().search([
                ('user_id', '=', request.env.user.id),
            ])

            recom_cases = action.mapped('recom_id').filtered(
                lambda r: r.status and not r.for_efs and r.project_id.id == project_id
            )

        values = {
            'project_sudo':project_sudo,
            'recom_cases':recom_cases,
            'message': message,
            'report_type': 'html',
        }
        
        #To get chatter in portal
        history_session_key = 'project_history'
        values = self._get_page_view_values(
            project_sudo, access_token, values, history_session_key, False)

        return request.render('in2it_forensic_services.ed_portal_projects', values)
    

    @http.route(['/my/cases/<int:case_id>'], type='http', auth="user", website=True)
    def portal_case_page(
        self,
        case_id,
        report_type=None,
        message=False,
        access_token=None,
        download=False,
        **kw
    ):
        try:
            case_sudo = self._document_check_access('forensic.case.assignment', case_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(
                model=case_sudo,
                report_type=report_type,
                report_ref='in2it_forensic_services.case_auth_pdf_report',
                download=download,
            )
        attachments = case_sudo.message_ids.mapped('attachment_ids')
        if attachments:
            attachments.generate_access_token()
        latest_attachment = attachments.filtered(lambda a: a.res_field == "signed")
        documents = False
        evidence = False
        if case_sudo:
            documents = request.env['forensic.document.line'].sudo().search([
                ('case_assignment_id','=',case_sudo.id)
            ])
            evidence = request.env['complaint.physical.item'].sudo().search([
                ('case_assignment_id','=',case_sudo.id)
            ])

            if evidence:
                evidence.attachment_ids.generate_access_token()
           

        document_types = request.env['forensic.document.type'].sudo().search([])
        values = {
            'case_record':case_sudo,
            'message': message,
            'report_type': 'html',
            'attachments': latest_attachment if latest_attachment else False,
            'documents':documents,
            'document_types':document_types,
            'evidence_records':evidence,
            # 'res_company': case_sudo.company_id,  # Used to display correct company logo
        }
        #To get chatter in portal
        history_session_key = 'my_case_history'
        values = self._get_page_view_values(
            case_sudo, access_token, values, history_session_key, False)

       

        return request.render('in2it_forensic_services.case_record_portal_template', values)
    

    @http.route('/my/upload_document', type='http', auth="user", methods=['POST'], csrf=True)
    def upload_document(self, **post):

        file = post.get('file')
        if not file:
            return request.redirect(request.httprequest.referrer)

        request.env['forensic.document.line'].sudo().create({
            'case_assignment_id': int(post.get('case_id')),
            'document_type_id': int(post.get('document_type_id')),
            'file': base64.b64encode(file.read()),
            'file_name': file.filename,
            'uploaded_by': request.env.user.id,
            'uploaded_date': fields.Date.today(),
        })

        return request.redirect(request.httprequest.referrer)
    
    @http.route('/my/add_evidence', type='http', auth="user", methods=['POST'], csrf=True)
    def add_evidence(self, **post):

        # Create evidence record
        item = request.env['complaint.physical.item'].sudo().create({
            'case_assignment_id': int(post.get('case_id')),
            'item_title': post.get('item_title'),
            'item_category': post.get('item_category'),
            'quantity': float(post.get('quantity') or 0),
        })

        # Handle attachments
        files = request.httprequest.files.getlist('attachments')
        for f in files:
            attachment = request.env['ir.attachment'].sudo().create({
                'name': f.filename,
                'datas': base64.b64encode(f.read()),
                'res_model': 'complaint.physical.item',
                'res_id': item.id,
                'type': 'binary',
            })
            item.attachment_ids = [(4, attachment.id)]

        return request.redirect(request.httprequest.referrer)
    
    @http.route('/my/upload_ed_report', type='http', auth='user', methods=['POST'], csrf=True)
    def upload_single_file(self, **post):
        case_id = int(post.get('case_id'))
        file = request.httprequest.files.get('file')

        if file:
            file_content = file.read()
            request.env['ir.attachment'].sudo().create({
                'name': file.filename,
                'type': 'binary',
                'datas': base64.b64encode(file_content),
                'res_model': 'forensic.case.assignment',
                'res_id': case_id,
                'assignment_id': case_id,
            })
            assignment = request.env['forensic.case.assignment'].sudo().browse(case_id)

            assignment.write({
                'file_data': base64.b64encode(file_content),
                'file_name': file.filename,
                'report_submitted_by': request.env.user.partner_id.id
            })
            env = request.env
            message = "Line Referral report is added for your review"
            model = assignment._name
            res_id = assignment.id
            group = (
                request.env.ref('in2it_project_management.group_cms_governance')
            ).sudo()

            users = group.users
            for user in users:
                user_id = user.id
                send_system_notification(env,message,model,user_id,res_id)

        return request.redirect(request.httprequest.referrer)
    