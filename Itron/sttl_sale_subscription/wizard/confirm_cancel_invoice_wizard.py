from odoo import fields, models


class ConfirmCancelInvoiceWizard(models.TransientModel):
    _name = 'confirm.cancel.invoice.wizard'
    _description = 'Confirm Cancel Draft Invoice Before Closing Subscription'

    invoice_id = fields.Many2one('account.move', string='Draft Invoice', readonly=True)
    subscription_id = fields.Many2one('sale.order', string='Subscription', readonly=True)
    closing_date = fields.Date(string='Closing Date', default=fields.Date.today())
    invoice_ids = fields.Many2many(
        'account.move',
        string='Draft Invoices',
        readonly=True
    )

    def action_confirm_cancel(self):
        for invoice in self.invoice_ids:
            if invoice.state == 'draft':
                invoice.button_cancel()

        self.subscription_id.subscription_status = 'c'
        msg = f"Subscription Closed. Draft invoices canceled: {', '.join(self.invoice_ids.mapped('name'))}"
        self.subscription_id.message_post(body=msg)
        self.subscription_id.closing_date = self.closing_date

        return {'type': 'ir.actions.act_window_close'}

    def action_abort(self):
        return {'type': 'ir.actions.act_window_close'}
