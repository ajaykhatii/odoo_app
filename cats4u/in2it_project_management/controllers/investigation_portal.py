# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

import binascii
from odoo import http,_
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.addons.in2it_forensic_services.models.case_assignment import send_system_notification

class InvestigationPortalmnnnnnnbmn(CustomerPortal):    

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        domain = self.prepare_domain()
        if 'tor_count' in counters:
            case_type = request.env['investigation.vendor.tor']
            try:
                count = case_type.search_count([('user_id','=',request.env.user.id),('status','=','to_approve')])
            except AccessError:
                count = 0
            values['tor_count'] = count
        if 'memo_pending_count' in counters:
            memos = request.env['overarching.memo'].sudo()
            user = request.env.user
            if user.position == 'ed':
                try:
                    count = memos.search_count([('status','=','pending'),('memo_pending_at','=','ed')])
                except AccessError:
                    count = 0
            else:
                count = 0 
            values['memo_pending_count'] = count
        return values
    

    @http.route(['/my/pending/tor'], type='http', auth="user", website=True)
    def authorise_case_mnbnmn(self, **kw):
        """Render the portal page for cases to authorize"""
        investigation_tor = request.env['investigation.vendor.tor'].sudo().search([('user_id','=',request.env.user.id),('status','=','to_approve')])
        values = self._prepare_portal_layout_values()
        
        values.update({
            'investigation_tor': investigation_tor,
            'page_name': 'tor_approval',
        })
        return request.render('in2it_project_management.portal_my_pending_tor', values)
    
    @http.route(['/my/tors/<int:tor_id>'], type='http', auth="user", website=True, methods=['GET', 'POST'])
    def portal_tor_page(self, tor_id, message=False, access_token=None, **kw):
        try:
            tor_sudo = self._document_check_access('investigation.vendor.tor', tor_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        values = {
            'tor_record':tor_sudo,
            'message': message,
            'report_type': 'html',
        }
        #To get chatter in portal
        history_session_key = 'my_tor_history'
        values = self._get_page_view_values(
            tor_sudo, access_token, values, history_session_key, False)
       
        if tor_sudo.status == 'to_approve':
            tor_approver_vals = {}
            if request.httprequest.method == 'POST':
                action = kw.get('action')
                update_remark = kw.get('update_remark')
                remark = kw.get('remark')

                if action == 'accept':
                    
                    tor_sudo.status = 'approved'
                    tor_sudo.user_id = False
                    tor_sudo.pfo_id = False
                    tor_sudo.approval_action = 'complete'
                    recipient = False
                    line_approval_action = 'ed'
            
                    # TOR APPROVER(S)
                    tor_approver_vals = {
                        'user_id': request.env.user.id,
                        'status':"approved",
                        'date':fields.datetime.now(),
                        'remark':remark if remark else '',
                        'approval_action' : line_approval_action,
                    }

                    new_vendor = tor_sudo.project_id.partner_line_ids.filtered(
                        lambda r: r.status == 'new'
                    )[:1]
                    new_vendor.action_send_weblink_to_vendor()
                    update_remark = kw.get('remark')
                    
                    message = "TOR request has been approved."
                    user_id = tor_sudo.project_id.assigned_pfo_id.id
                    res_id = tor_sudo.id
                    model = tor_sudo._name
                    
                if action == 'send_for_update':
                    if not update_remark:
                        raise ValidationError("Remark is required for updates.")
                    tor_sudo.status = 'draft'
                    tor_sudo.approval_action = False
                    tor_sudo.pfo_id = tor_sudo.project_id.assigned_pfo_id.id
                    tor_sudo.user_id = tor_sudo.project_id.assigned_pfo_id.id
                    recipient = tor_sudo.pfo_id

                    message = "TOR request waiting for your update"
                    user_id = recipient.id
                    res_id = tor_sudo.id
                    model = tor_sudo._name

                # TOR LOG COMMENT FOR APPROVAL AND SEND FOR UPDATES
                tor_comment_vals = {
                    'sender_id': request.env.user.id,
                    'recipient_id':recipient.id if recipient else False,
                    'sent_date':fields.datetime.now(),
                    'remark':update_remark if update_remark else remark,
                }
                
                tor_sudo.write({
                    'tor_line_ids': [(0, 0, tor_comment_vals)],
                    'approver_line_ids': [(0, 0, tor_approver_vals)] if tor_approver_vals else []
                }) 
                if user_id and res_id and model:
                    send_system_notification(request.env,message,model,user_id,res_id)
                return request.redirect('/my/pending/tor')
        return request.render('in2it_project_management.investigation_record_portal_template', values)
    