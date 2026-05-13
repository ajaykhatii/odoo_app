# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2026 (https://www.in2ittech.com)
#
##############################################################################

from odoo import http, fields
from odoo.http import request


class TorVendorApproval(http.Controller):


    @http.route('/vendor/tor/<int:project_id>/<string:token>', methods=['GET', 'POST'], type="http", website=True, csrf=True, auth='public')
    def action_send_tor_to_vendor(self, token, project_id, **kwargs):
        vendor = request.env['investigation.vendor.line'].sudo().search([('project_id','=',project_id),('token','=',token)])
        tor = request.env['investigation.vendor.tor'].sudo().search([('project_id','=',project_id),('status','=','approved')], limit=1)
        approvers = tor.approver_line_ids.filtered(lambda p : p.tor_id == tor).sorted('create_date', reverse=True)[:3]

        investigation_manager = approvers.filtered(lambda p : p.approval_action == 'investigation_manager')
        chief = approvers.sudo().filtered(lambda p : p.approval_action == 'chief')
        ed = approvers.sudo().filtered(lambda p : p.approval_action == 'ed')


        if not vendor:
            return request.render('in2it_project_management.form_invalid_token', {'name':'Invalid Link'})
        
        if vendor:
            if request.httprequest.method == 'GET':
                if vendor.expiration_date and vendor.expiration_date < fields.Datetime.now() :
                    return request.render('in2it_project_management.form_invalid_token', {'name':'Link Expired'})

                if vendor.status in ['accept','reject']:
                    return request.render('in2it_project_management.in2it_vendor_tor_approval', 
                        {
                            'token':token, 
                            'vendor':vendor, 
                            'tor':tor,
                            'is_submit':True,
                        }
                    )
                else:
                    return request.render('in2it_project_management.in2it_vendor_tor_approval', 
                        {
                            'token':token, 
                            'vendor':vendor, 
                            'tor':tor,
                            'is_submit':False
                        }
                    )            

            if request.httprequest.method == 'POST':
                vendor = vendor.search([('token','=',token)])
                action = kwargs.get('action')
                vendor.status = action
                if vendor.status == 'accept':
                    vendor.project_id.stage_id = request.env.ref('project.project_project_stage_1').sudo().id
                vendor.action_date = fields.Datetime.now()
                return request.render('in2it_project_management.form_verification_thank_you')

                


