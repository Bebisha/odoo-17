from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AttachmentValidationWizard(models.TransientModel):
    _name = 'attachment.validation.wizard'
    _description = 'Attachment Validation Wizard'

    @api.model
    def default_get(self, fields_list):
        res = super(AttachmentValidationWizard, self).default_get(fields_list)
        sale_order_ids = self.env.context.get('active_ids', [])
        missing_attachments = []
        for sale in self.env['sale.order'].browse(sale_order_ids):
            sale_missing_attachments = sale.checklist_line_ids.filtered(lambda x: not x.checkbox).mapped('processing_document_id.name')
            if sale_missing_attachments:
                missing_attachments.append(f"Sale Order {sale.name}: " + ", ".join(sale_missing_attachments))
        if missing_attachments:
            message = "The following attachments are missing:\n" + "\n".join(missing_attachments)
        else:
            message = "Attached all required documents !"
        res.update({
            'message': message,
        })

        return res

    sale_order_ids = fields.Many2many('sale.order', string='Sale Orders',
                                      default=lambda self: self._get_sale_order_ids())
    message = fields.Text(string='Message', readonly=True)

    def _get_sale_order_ids(self):
        return self.env.context.get('active_ids', [])

    def create_invoice(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.advance.payment.inv',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_ids': self.sale_order_ids.ids,
            },
        }

