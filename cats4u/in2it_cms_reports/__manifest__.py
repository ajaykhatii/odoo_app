# -*- encoding: utf-8 -*-
##############################################################################
#
#    In2IT Technologies Pvt. Ltd
#    Copyright (C) 2025 (https://www.in2ittech.com)
#
##############################################################################
{
    'name': 'In2it CMS Reports',
    'description': """
        In2it CMS Reports
    """,
    'summary':'In2it CMS Reports',
    'version': '0.18.1',
    'license': 'LGPL-3',
    'category':'Tool',
    'website': 'https://www.in2ittech.com',
    'author': 'In2IT Technologies Pvt. Ltd.',
    'depends': ['in2it_forensic_services', 'in2it_project_management'],
    'data': [
        "data/cms_reports_data.xml",
        "security/ir.model.access.csv",
        "wizards/cms_reports_wizard_view.xml",
        "views/cms_reports_view.xml",
    ],

	'images': [
        'static/description/icon.png'
    	],
    'installable': True

}

