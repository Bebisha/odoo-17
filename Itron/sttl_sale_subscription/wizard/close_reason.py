from odoo import fields, models

class CloseReasonWizard(models.TransientModel):
    _name = 'close.reason.wizard'

    reason_id = fields.Many2one(comodel_name='close.reason', string='Reason',required=True)
    closing_date = fields.Date(string='Closing Date', default=fields.Date.today())
    

    def action_close_subs(self):
        subs_id = self.env.context.get('rec_id')
        if not subs_id:
            return

        subscription = self.env['sale.order'].browse(subs_id)
        draft_invoice = self.env['account.move'].search([
            ('kg_sale_order_id', '=', subscription.id),
            ('state', '=', 'draft')
        ])

        if draft_invoice:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Confirm Invoice Cancellation',
                'res_model': 'confirm.cancel.invoice.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                     'default_invoice_ids': [(6, 0, draft_invoice.ids)],
                    'default_subscription_id': subscription.id,
                    'default_closing_date':self.closing_date,
                }
            }
        else:
            subscription.subscription_status = 'c'
            msg = "Subscription Closed : Reason - " + self.reason_id.desc
            subscription.message_post(body=msg)
            subscription.closing_date = self.closing_date

        return {'type': 'ir.actions.act_window_close'}
