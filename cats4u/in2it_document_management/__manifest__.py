# -*- coding: utf-8 -*-
{
    'name': 'In2IT Document Management',
    'version': '18.0',
    'description': """ Document Management """,
    'category': 'Documents',
    'summary': """In2IT Document Management""",
    'website': 'https://www.in2ittech.com/',
    "author": "[Odoo Team] In2IT Global Systems & Services",
    "maintainers": "In2IT Global Systems & Services'",
    'depends': ['base', 'documents_project', 'documents','in2it_project_management'],
    'data': [
    ],
    
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',

    'post_init_hook': 'post_init_create_repo_structure',
}

