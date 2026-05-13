from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64


class ProjectDocumentManagement(models.Model):
    _inherit = "project.project"


    def _create_missing_folders(self):
        super()._create_missing_folders()

        Document = self.env['documents.document']

        subfolders = {
            'Annexures': 'annexure',
            'Exhibits': 'exhibits',
            'Final Report': 'final_report',
            'Authorization Objectives': 'auth_obj',
            'Correspondence': 'correspondence',
            'Litigation': 'litigation',
            'Recommendation Implementation': 'recom_imp',
            'Documents': 'doc'
        }

        for project in self:
            parent = project.documents_folder_id
            if not parent:
                continue

            if not parent.active:
                parent.write({'active': True})

            # Check existing subfolders
            existing_folders = Document.search([
                ('folder_id', '=', parent.id),
                ('type', '=', 'folder'),
                ('active', '=', True)
            ]).mapped('name')
            
            for name, code in subfolders.items():
                if name not in existing_folders:
                    Document.create({
                        'name': name,
                        'type': 'folder',
                        'folder_id': parent.id,
                        'doc_type': code
                    })


    def generate_soc_document(self):
        Document = self.env['documents.document']
        Attachment = self.env['ir.attachment']

        for project in self:
            if not project.documents_folder_id:
                project._create_missing_folders()

            if not project.documents_folder_id or not project.assignment_id:
                continue

            correspondence_folder = Document.search([
                ('folder_id', '=', project.documents_folder_id.id),
                ('type', '=', 'folder'),
                ('doc_type', '=', 'correspondence'),
                ('active', '=', True)
            ], limit=1)

            if not correspondence_folder:
                continue

            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                'in2it_forensic_services.action_report_forensic_case_assignment_pdf',
                [project.assignment_id.id]
            )

            attachment = Attachment.create({
                'name': 'Schedule of Complaints.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'project.project',
                'res_id': project.id,
                'mimetype': 'application/pdf',
            })

            # Find auto-created document
            document = Document.search([
                ('attachment_id', '=', attachment.id)
            ], limit=1)


            # Update it (DO NOT CREATE NEW)
            if document:
                document.write({
                    'name': 'Schedule of Complaints',
                    'folder_id': correspondence_folder.id,
                    'doc_type': 'correspondence',
                    'res_model': 'project.project',
                    'res_id': project.id,
                    'owner_id': self.env.user.id,
                })


    def auth_letter(self):
        Document = self.env['documents.document']
        Attachment = self.env['ir.attachment']

        for project in self:
            parent = project.documents_folder_id
            if not parent:
                continue

            if not parent.active:
                parent.write({'active': True})
            

            # Handle Authorization Objective document
            if project.assignment_id:
                latest_attachment = Attachment.search([
                    ('res_model', '=', 'forensic.case.assignment'),
                    ('res_id', '=', project.assignment_id.id),
                    ('res_field', '=', 'signed')
                ], order='create_date desc', limit=1)
                if latest_attachment:
                    subfolder = Document.search([
                        ('folder_id', '=', parent.id),
                        ('type', '=', 'folder'),
                        ('doc_type', '=', 'auth_obj'),
                        ('active', '=', True)
                    ], limit=1)

                    if subfolder:
                        project._sync_document_to_folder(
                            subfolder,
                            project,
                            latest_attachment.name,
                            latest_attachment,
                            'auth_obj'
                        )



    @api.model_create_multi
    def create(self,vals_list):
        projects = super().create(vals_list)

        projects.generate_soc_document()
        projects.auth_letter()

        return projects
        

    def _sync_document_to_folder(self, folder, project, name, attachment, doc_type):
        Document = self.env['documents.document']

        if not folder or not attachment:
            return

        existing_doc = Document.search([
            ('attachment_id', '=', attachment.id)
        ], limit=1)

        vals = {
            'name': name,
            'attachment_id': attachment.id,
            'folder_id': folder.id,
            'doc_type': doc_type,
            'res_model': 'project.project',
            'res_id': project.id,
            'owner_id': self.env.user.id,
        }

        if existing_doc:
            existing_doc.write(vals)
        else:
            Document.create(vals)

        
    def write(self, vals):
        res = super().write(vals)

        Document = self.env['documents.document']
        Attachment = self.env['ir.attachment']

        for project in self:
            if not project.documents_folder_id:
                project._create_missing_folders()

            folder = project.documents_folder_id
            if not folder:
                continue

            if folder and not folder.active:
                folder.write({'active': True})

            # ------------------ EXHIBITS ------------------
            exhibit_folder = Document.search([
                ('folder_id', '=', folder.id),
                ('type', '=', 'folder'),
                ('doc_type', '=', 'exhibits'),
                ('active', '=', True)
            ], limit=1)

            items = self.env['complaint.physical.item'].search([
                ('project_id', '=', project.id),
                ('is_exhibit', '=', True),
                ('attachment_ids', '!=', False)
            ])

            for item in items:
                for attachment in item.attachment_ids:
                    self._sync_document_to_folder(
                        exhibit_folder,
                        project,
                        attachment.name,
                        attachment,
                        'exhibits'
                    )

            # ------------------ ANNEXURE ------------------
            annexure_folder = Document.search([
                ('folder_id', '=', folder.id),
                ('type', '=', 'folder'),
                ('doc_type', '=', 'annexure')
            ], limit=1)

            annexure_docs = self.env['forensic.document.line'].search([
                ('project_id', '=', project.id),
                ('is_annexure', '=', True),
                ('file', '!=', False)
            ])

            for doc in annexure_docs:
                attachment = Attachment.search([
                    ('res_model', '=', 'forensic.document.line'),
                    ('res_id', '=', doc.id),
                    ('res_field', '=', 'file')
                ], limit=1)

                self._sync_document_to_folder(
                    annexure_folder,
                    project,
                    doc.file_name,
                    attachment,
                    'annexure'
                )

            # ------------------ EVIDENCE ------------------
            doc_folder = Document.search([
                ('folder_id', '=', folder.id),
                ('type', '=', 'folder'),
                ('doc_type', '=', 'doc'),
                ('active', '=', True)
            ], limit=1)

            evidence_docs = self.env['forensic.document.line'].search([
                ('project_id', '=', project.id),
                ('file', '!=', False),
                ('is_annexure', '=', False)
            ])

            for doc in evidence_docs:
                attachment = Attachment.search([
                    ('res_model', '=', 'forensic.document.line'),
                    ('res_id', '=', doc.id),
                    ('res_field', '=', 'file')
                ], limit=1)

                self._sync_document_to_folder(
                    doc_folder,
                    project,
                    doc.file_name,
                    attachment,
                    'doc'
                )

        return res    


class DocumentManagement(models.Model):
    _inherit = "documents.document"
    _order = 'name desc'

    doc_type = fields.Selection([('annexure','Annexure'),('exhibits','Exhibits'),('final_report','Final Reports'),('auth_obj','Authorization Objectives'),('correspondence','Correspondence'),('litigation','Litigation'),('recom_imp','Recommendation Implementation'),('doc','Documents')])

    @api.constrains('name', 'folder_id', 'type')
    def _check_unique_folder(self):
        for record in self:
            if record.type == 'folder':
                domain = [
                    ('id', '!=', record.id),
                    ('name', '=ilike', record.name),
                    ('folder_id', '=', record.folder_id.id),
                    ('type', '=', 'folder'),
                ]

                duplicate = self.search(domain, limit=1)
                if duplicate:
                    raise ValidationError(
                        f"Folder '{record.name}' already exists in this location."
                    )
                

                
class VendorDocument(models.TransientModel):
    _inherit = 'outsource.review.docs'

    @api.model_create_multi
    def create(self, vals_list):
        record = super().create(vals_list)

        # Get project from context
        project_id = self.env.context.get('active_id')
        project = self.env['project.project'].browse(project_id)
  
        if not project or not project.documents_folder_id:
            return record

        Document = self.env['documents.document']

        # Find Correspondence folder
        correspondence_folder = Document.search([
            ('folder_id', '=', project.documents_folder_id.id),
            ('type', '=', 'folder'),
            ('doc_type', '=', 'correspondence'),
            ('active', '=', True)
        ], limit=1)

        if not correspondence_folder:
            return record
        
        for attachment in record.attachment_ids:
            project._sync_document_to_folder(
                correspondence_folder,
                project,
                attachment.name,
                attachment,
                'correspondence'
            )

        return record
    


class PeerReviewSignOffWizard(models.TransientModel):
    _inherit = 'peer.review.signoff.wizard'

    def action_submit(self):
        res = super().action_submit()

        review_id = self.env.context.get('active_id')
        review = self.env['forensic.peer.review'].browse(review_id)
        project = review.project_id
       
        if not project or not project.documents_folder_id:
            raise ValidationError("Project folder not found!")

        Document = self.env['documents.document']
        project_folder = project.documents_folder_id

        # Find Final Report folder
        report_folder = Document.search([
            ('folder_id', '=', project_folder.id),
            ('type', '=', 'folder'),
            ('doc_type', '=', 'final_report'),
            ('active', '=', True)
        ], limit=1)

        case_type = project.assignment_type_id.name  

        if case_type == 'PRE':
            report_xml = 'in2it_project_management.action_pre_investigation_report'
            record_id = project.id  
        else:
            report_xml = 'in2it_project_management.action_investigation_report'
            record_id = project.id

        if not report_xml:
            raise ValidationError("Report not found.!")

        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            report_xml,
            [record_id]
        )

        # File name based on case
        file_name = (
            f"Assessment Report.pdf"
            if case_type == 'PRE'
            else f"Investigation Report.pdf"
        )

        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'mimetype': 'application/pdf',
            'res_model': 'forensic.peer.review',
            'res_id': review.id,
        })
      
        project._sync_document_to_folder(
            report_folder,
            project,
            attachment.name,
            attachment,
            'final_report'
        )

        return res
    


class TORDocument(models.Model):
    _inherit = 'tor.remark.wizard'

    
    def action_approve_tor_wizard(self):
        res = super().action_approve_tor_wizard()

        tor_id = self.env.context.get('active_id')
        tor = self.env['investigation.vendor.tor'].browse(tor_id)
        project = tor.project_id

        if not project or not project.documents_folder_id:
            return

        Document = self.env['documents.document']

        reports_folder = Document.search([
            ('folder_id', '=', project.documents_folder_id.id),
            ('type', '=', 'folder'),
            ('doc_type', '=', 'final_report'),
            ('active', '=', True)
        ], limit=1)
       
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                'in2it_project_management.vendor_accept_tor_report_action',
                [tor.id]
            )

        self.env['ir.attachment'].create({
            'name': f'TOR Report.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'investigation.vendor.tor',
            'res_id': tor.id,                     
            'mimetype': 'application/pdf',
        })
        
        latest_attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'investigation.vendor.tor'),
            ('res_id', '=', tor.id)
        ], order='id desc', limit=1)


        if not latest_attachment:
            return res

        existing_doc = self.env['documents.document'].search([
            ('folder_id', '=', reports_folder.id),
            ('doc_type', '=', 'final_report')
        ], limit=1)

        if existing_doc:
            existing_doc.write({
                'attachment_id': latest_attachment.id,
                'name': latest_attachment.name,
            })
        else:
            project._sync_document_to_folder(
                reports_folder,
                project,
                latest_attachment.name,
                latest_attachment,
                'final_report'
            )
        return res  
