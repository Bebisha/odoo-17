import base64
import time
import odoo.http as http
from odoo.http import request


class HelpdeskTicketController(http.Controller):

    @http.route("/add/customer_documents", type="http", auth="user", website=True)
    def add_customer_documents(self, **kw):
        user = request.env.user
        domain = []
        if user.has_group('base.group_portal'):
            domain += [('id', '=', user.partner_id.id)]
        customer = http.request.env["res.partner"].sudo().search(domain)
        folders = http.request.env["documents.folder"].sudo().search([])
        return http.request.render("kg_raw_fisheries_documents_portal.add_customer_documents_template", {
            "customers": customer,
            "folders": folders,
        })

    @http.route("/submitted/document", type="http", auth="user", website=True, csrf=True)
    def submit_document(self, **kw):
        partner_id = int(kw.get("customer"))
        folder_id = int(kw.get("folder"))
        partner = request.env["res.partner"].sudo().browse(partner_id)
        folder = request.env["documents.folder"].sudo().browse(folder_id)
        upload_file = kw.get('upload_file')
        if upload_file:
            file_content = upload_file.read()
            encoded_file = base64.b64encode(file_content)
            filename = upload_file.filename
            vals = {
                'name': filename,
                'partner_id': partner.id,
                'datas': encoded_file,
                'folder_id': folder.id,
                'res_id': partner.id,
                'res_model': 'res.partner',
                'type': 'binary',
                'owner_id': request.env.user.id,
            }
            new_document = request.env['documents.document'].sudo().create(vals)
            return request.render("kg_raw_fisheries_documents_portal.thank_you_page_template")
            # return werkzeug.utils.redirect("/my/documents/%s" % new_document.id)

    @http.route(["/my/documents/<int:document_id>"], type="http", auth="public", website=True)
    def portal_my_documents(self, document_id=None, access_token=None, **kw):
        document = request.env['documents.document'].sudo().search([('id', '=', document_id)])
        return request.render("kg_raw_fisheries_documents_portal.customer_own_documents_template", {
            'document': document
        })

    @http.route("/view/transaction_documents", type="http", auth="user", website=True)
    def view_transaction_documents(self, **kw):
        user = request.env.user
        domain = [('state', '=', 'submit')]
        if user.has_group('base.group_portal'):
            domain += [('partner_id', '=', user.partner_id.id)]

        selected_status = kw.get('status')
        if selected_status:
            domain.append(('status', '=', selected_status))

        documents = request.env['transaction.documents.line'].sudo().search(domain)
        timestamp = int(time.time())

        return request.render("kg_raw_fisheries_documents_portal.view_transaction_documents_template", {
            'documents': documents, 'timestamp': timestamp, 'selected_status': selected_status,
        })

    @http.route(['/document/approve/<int:doc_id>'], type='http', auth='user')
    def approve_document(self, doc_id):
        doc = request.env['transaction.documents.line'].sudo().browse(doc_id)
        if doc.exists():
            if request.env.user.partner_id.id != doc.partner_id.id:
                return self._popup_response('You have no access to approve!')
            doc.action_approve()
        return request.redirect('/view/transaction_documents')

    @http.route('/document/reject/<int:doc_id>', type='http', auth='user', website=True)
    def reject_document(self, doc_id, **kwargs):
        doc = request.env['transaction.documents.line'].sudo().browse(doc_id)
        return request.render(
            'kg_raw_fisheries_documents_portal.transaction_documents_reject_template',
            {'doc': doc}
        )

    @http.route('/document/reject/submit/<int:doc_id>', type='http', auth='user', website=True)
    def submit_rejection(self, doc_id, **kw):
        reason = kw.get('reason')
        doc = request.env['transaction.documents.line'].sudo().browse(doc_id)
        doc.write({'status': 'rejected', 'reject_reason': reason})

        mail_values = {
            'subject': f'Document Rejected: {doc.name or "Transaction Document"}',
            'body_html': f"""
                        <p>Dear {doc.transaction_document_id.user_id.name},</p>
                        <p>Your document <b>{doc.name or "Transaction Document"}</b> has been <b>rejected</b>.</p>
                        <p><b>Reason:</b> {reason or 'No reason provided.'}</p>
                        <p>Please review and resubmit if necessary.</p>
                        <br/>
                        <p>Regards,<br/>{doc.partner_id.name or 'System'}</p>
                    """,
            'email_to': doc.transaction_document_id.user_id.email,
            'email_from': doc.partner_id.email or request.env.user.email,
        }

        mail = request.env['mail.mail'].sudo().create(mail_values)
        mail.sudo().send()

        return request.redirect('/view/transaction_documents')

    @staticmethod
    def _popup_response(message):
        return f"""
            <html>
                <head>
                    <script>
                        alert('{message}');
                        window.history.back();
                    </script>
                </head>
                <body></body>
            </html>
        """
