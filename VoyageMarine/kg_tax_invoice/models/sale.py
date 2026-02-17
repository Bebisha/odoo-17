import ast
import base64
from datetime import datetime

from odoo.tools import formatLang, float_is_zero
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, _, api
import werkzeug
import re
from ast import literal_eval


class KGSaleInherit(models.Model):
    _inherit = "sale.order"
    _description = 'Quotation'

    def action_quotation_send(self):
        res = super(KGSaleInherit, self).action_quotation_send()
        # if res and self.state == 'draft':
        #     self.proforma_invoice_no = self.env['ir.sequence'].next_by_code('proforma.inv')
        if self.env.context.get('proforma'):
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                "kg_tax_invoice.standard_pdf_tax_invoice_report",
                [self.id])
            file_name = str('PRO-FORMA-') + str(self.name)
        else:
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                "kg_tax_invoice.standard_pdf_tax_invoice_report", [self.id])
            if self.state in ['draft', 'sent']:
                file_name = str('Quotation-') + str(self.name)
            else:
                file_name = str('Order-') + str(self.name)

        if isinstance(pdf_content, bytes):
            encoded_pdf = base64.b64encode(pdf_content)

            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': encoded_pdf.decode(),
                'res_model': 'sale.order',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })

            if 'context' in res:
                res['context']['default_attachment_ids'] = [(4, attachment.id)]

            else:
                res['context'] = {'default_attachment_ids': [(4, attachment.id)]}

        return res


