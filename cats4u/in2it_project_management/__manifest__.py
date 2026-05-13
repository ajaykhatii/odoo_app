# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################

{
    'name': 'In2it Project Management',
    'description': """
        In2it Project Management
    """,
    'summary':'In2it Project Management',
    'version': '0.18.1',
    'license': 'LGPL-3',
    'category':'base',
    'website': 'https://www.in2ittech.com',
    'author': '[Pawan Kumar] In2IT Technologies.',
    'maintainer': 'Pawan Kumar',
    'depends': ['base', 'project', 'in2it_forensic_services','timesheet_grid','web','in2it_system_notification'],
    'data': [
        'security/cms_project_security.xml',
        "security/ir.model.access.csv",
        'data/project_data.xml',
        'data/background_database.xml',
        'data/recommendation_category.xml',
        "data/standard_task_category.xml",
        "data/project_task_stages.xml",
        "data/mail_templates.xml",
        "data/evidence_letter.xml",
        "data/digital_evidence_sequence.xml",
        "data/overarching_memo_letter.xml",
        "data/sign_data.xml",
        "views/res_config_settings_views.xml",
        "reports/request_digital_access_cm_report.xml",
        "reports/overarching_pre_memo_report.xml",
        "reports/vendor_tor_report.xml",
        "wizard/assign_standard_task_wizard_views.xml",
        "wizard/remark_wizard.xml",
        "wizard/request_access_digital_wizard_view.xml",
        "wizard/request_digital_wizard_views.xml",
        "wizard/assign_pm_wizard_views.xml",
        "wizard/overarching_memo_wizard_views.xml",
        "wizard/overarching_wizard_view.xml",
        "wizard/tor_remark.xml",
        "wizard/recommendation_wizard.xml",
        "reports/cms_qweb_report_view.xml",
        "views/forensic_views.xml",
        "views/investigation_dir_dept_view.xml",
        "views/project_views.xml",
        "views/standard_task_views.xml",
        "views/project_task_views.xml",
        "views/in2it_public_holidays_views.xml",
        "views/resource_calendar_views.xml",
        'views/role_player_views.xml',
        "views/background_check_views.xml",
        "views/assign_forensic_team_views.xml",
        "reports/investigation_report.xml",
        "reports/pre_investigation_report.xml",
        "wizard/investigation_report.xml",
        "wizard/forensic_team_wizard.xml",
        "wizard/assign_vendor_wizard_views.xml",  
        "templates/tor_tempates.xml",
        "templates/ed_tor_template.xml",
        "wizard/peer_review_wizard_views.xml",
        "wizard/peer_review_signoff_wizard_views.xml",
        "views/menuitem.xml",
        "views/project_meeting_view.xml",
        "views/digital_evidence_views.xml",
        "views/forensic_peer_review_views.xml",
        "views/overarching_memo_views.xml",
        "views/project_tor_views.xml",
        "views/project_vendor_views.xml",
        "views/project_recommendation_views.xml",
        "views/team_change_request_view.xml",
        "views/sign_portal_template_inherit.xml",
        "views/sign_request_template.xml",
        "views/ed_portal_view.xml",
        "wizard/line_update_views.xml",
        "wizard/case_close_wizard_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            "in2it_project_management/static/src/xml/cm_sign_template.xml",
            "in2it_project_management/static/src/js/cm_sign_template.js",
            "in2it_project_management/static/src/one2many_tags/**/*",
        ],
    },

	'images': [
        'static/description/icon.png'
    	],
    'installable': True

}