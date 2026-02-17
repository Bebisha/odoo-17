from odoo import models, fields,api


class InvoiceAttachMaster(models.Model):
    _name = "invoice.attachment.master"
    _description = "Invoice Attachment Master"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Attachment")
    bill_type = fields.Selection([
        ('customer', 'Customer Bill'),
        ('vendor', 'Vendor Bill')
    ], string="Bill Type", required=True, tracking=True,)  # Default is 'customer'

    invoice_id = fields.Many2one('account.move', string="Invoice")

    # @api.model
    # def create(self, vals):
    #     # Check if 'bill_type' is not provided and 'invoice_id' is provided
    #     if not vals.get('bill_type') and vals.get('invoice_id'):
    #         invoice = self.env['account.move'].browse(vals['invoice_id'])
    #
    #         # Set the 'bill_type' based on the 'move_type' of the invoice
    #         if invoice.move_type == 'out_invoice':
    #             vals['bill_type'] = 'customer'
    #         elif invoice.move_type == 'in_invoice':
    #             vals['bill_type'] = 'vendor'
    #
    #     # Call the super method to create the record
    #     return super(InvoiceAttachMaster, self).create(vals)
    #
