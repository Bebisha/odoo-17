from odoo import models,api


class KGAccountMoveSendInherit(models.TransientModel):
    _inherit = "account.move.send"

    @api.model
    def _get_placeholder_mail_template_dynamic_attachments_data(self, move, mail_template):
        invoice_template = self.env.ref('kg_raw_fisheries_accounting.action_report_tax_invoice')
        extra_mail_templates = mail_template.report_template_ids - invoice_template
        filename = move._get_invoice_report_filename()
        return [
            {
                'id': f'placeholder_{extra_mail_template.name.lower()}_{filename}',
                'name': f'{extra_mail_template.name.lower()}_{filename}',
                'mimetype': 'application/pdf',
                'placeholder': True,
                'dynamic_report': extra_mail_template.report_name,
            } for extra_mail_template in extra_mail_templates
        ]

    @api.model
    def _prepare_invoice_pdf_report(self, invoice, invoice_data):
        """ Prepare the pdf report for the invoice passed as parameter.
        :param invoice:         An account.move record.
        :param invoice_data:    The collected data for the invoice so far.
        """
        if invoice.invoice_pdf_report_id:
            return

        content, _report_format = self.env['ir.actions.report'] \
            .with_company(invoice.company_id) \
            .with_context(from_account_move_send=True) \
            ._render('kg_raw_fisheries_accounting.action_report_tax_invoice', invoice.ids)

        invoice_data['pdf_attachment_values'] = {
            'raw': content,
            'name': invoice._get_invoice_report_filename(),
            'mimetype': 'application/pdf',
            'res_model': invoice._name,
            'res_id': invoice.id,
            'res_field': 'invoice_pdf_report_file',  # Binary field
        }

    @api.model
    def _prepare_invoice_proforma_pdf_report(self, invoice, invoice_data):
        """ Prepare the proforma pdf report for the invoice passed as parameter.
        :param invoice:         An account.move record.
        :param invoice_data:    The collected data for the invoice so far.
        """
        content, _report_format = self.env['ir.actions.report'].with_company(invoice.company_id)._render(
            'kg_raw_fisheries_accounting.action_report_tax_invoice', invoice.ids, data={'proforma': True})

        invoice_data['proforma_pdf_attachment_values'] = {
            'raw': content,
            'name': invoice._get_invoice_proforma_pdf_report_filename(),
            'mimetype': 'application/pdf',
            'res_model': invoice._name,
            'res_id': invoice.id,
        }
