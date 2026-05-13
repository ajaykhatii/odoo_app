from odoo import api, SUPERUSER_ID

def post_init_create_repo_structure(env):
    projects = env['project.project'].search([
        ('use_documents', '=', True)
    ])

    projects._create_missing_folders()