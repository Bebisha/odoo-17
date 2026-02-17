import base64

from odoo import models, fields, api

class ProformaInvoice(models.Model):
    _name = 'custom.proforma.invoice'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Custom Proforma Invoice'

    name = fields.Char(default='New', readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True, readonly=True)
    partner_id = fields.Many2one(related='sale_order_id.partner_id', store=True)
    date = fields.Date(default=fields.Date.context_today)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
    ], default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('proforma.inv')
        return super().create(vals)

    def action_send_proforma(self):
        """ Opens a wizard to compose an email, with relevant mail template loaded by default """
        self.ensure_one()
        mail_template = self.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf("sale.action_report_pro_forma_invoice", [self.sale_order_id.id])
        attachment = False
        if isinstance(pdf_content, bytes):
            encoded_pdf = base64.b64encode(pdf_content)

            attachment = self.env['ir.attachment'].create({
                'name': f'Proforma_{self.sale_order_id.name}.pdf',
                'type': 'binary',
                'datas': encoded_pdf.decode(),
                'res_model': 'sale.order',
                'res_id': self.sale_order_id.id,
                'mimetype': 'application/pdf',
            })

        ctx = {
            'default_model': 'sale.order',
            'default_res_ids': self.sale_order_id.ids,
            'default_template_id': mail_template.id if mail_template else None,
            'default_composition_mode': 'comment',
            'mark_proforma_as_sent': True,
            'default_email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'default_attachment_ids': [(4, attachment.id)],
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

