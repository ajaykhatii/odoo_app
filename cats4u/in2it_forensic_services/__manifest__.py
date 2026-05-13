# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

{
    'name': 'In2IT Forensic Services',
    'description': """
        CRM Case Registration
    """,
    'summary':'CRM Case Registraction',
    'version': '0.18.1',
    'license': 'LGPL-3',
    'category':'base',
    'website': 'https://www.in2ittech.com',
    'author': '[Pawan Kumar] In2IT Technologies.',
    'maintainer': 'Pawan Kumar',
    'depends': ['base', 'crm', 'uom', 'sign', 'hr','mail','in2it_extra_functionality_removal'],
    'data': [
        'security/fcm_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/assignment_stage_data.xml',
        'data/assignment_type.xml',
        'data/authorisation_report.xml',
        'data/authorisation_mail_template.xml',
        'data/case_type_authorisation_letter.xml',
        'data/tag_data.xml',
        'data/department_unit_data.xml',
        'data/document_type_data.xml',
        'data/date_and_time_sign_item_type.xml',
        'wizard/authorisation_wizard.xml',
        'wizard/case_assignment_views.xml',
        'wizard/case_revised_wizard_views.xml',
        'wizard/change_request_views.xml',
        'wizard/case_unauthorized_wizard.xml',
        'views/crm_lead_forensic_custom_views.xml',
        'views/config_master_views.xml',
        'views/case_assignment_views.xml',
        'views/hr_views.xml',
        'views/vendor_onboarding_views.xml',
        'views/crm_config_settings_views.xml',
        'views/forensic_portal_template.xml',
        'views/menu_views.xml',
        'views/crm_lead_activity_inherited.xml',
        'wizard/schedule_of_complaints_display_views.xml',
        'reports/report_city_manager_home_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css',
            'in2it_forensic_services/static/src/js/*.js',
            'in2it_forensic_services/static/src/xml/sign_thank_you.xml',
            'in2it_forensic_services/static/src/xml/hide_refuse_edit.xml',
        ],
        'web.assets_backend_lazy': [
            'in2it_forensic_services/static/src/xml/activity_header_inherit.xml',
        ],
        'web.assets_frontend': [
            'in2it_forensic_services/static/src/xml/sign_thank_you.xml',
        ],

        'sign.assets_public_sign': [
            'in2it_forensic_services/static/src/js/date_time_sign_type.js',
            'in2it_forensic_services/static/src/js/thank_you_dialog.js',
            'in2it_forensic_services/static/src/xml/sign_thank_you.xml',
            'in2it_forensic_services/static/src/scss/sign_document.scss'
        ],
    },

	'images': [
        'static/description/icon.png'
    	],
    'installable': True

}