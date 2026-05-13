# -*- coding: utf-8 -*-
{
    'name': 'In2IT Extra Functionality Removal',
    'version': '18.0',
    'description': """ This module aim is to remove extra functionality. """,
    'category': 'Extra Functionality Removal',
    'summary': """In2IT Extra Functionality Removal""",
    'website': 'https://www.in2ittech.com/',
    "author": "[Odoo Team] In2IT Global Systems & Services",
    "maintainers": "In2IT Global Systems & Services'",
    'depends': ['base', 'crm', 'hr_timesheet'],
    'data': [
        'views/extra_functionality_removal.xml'
    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}

