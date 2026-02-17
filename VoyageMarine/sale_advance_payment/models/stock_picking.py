from odoo.exceptions import UserError

from odoo import models


class KGSaleAdvanceStockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        if self.origin:
            sale_id = self.env['sale.order'].search([('name','=',self.origin)])
            if sale_id and sale_id.pre_payment:
                non_cancelled_payments = sale_id.account_payment_ids.filtered(lambda payment: payment.state != 'cancel')

                invoice_id = self.env['account.move'].search(
                    [('sale_id', '=', sale_id.id), ('state', '=', 'posted')])

                if not non_cancelled_payments and not invoice_id:
                    raise UserError("Please make the advance payment before validating the order")
        return super(KGSaleAdvanceStockPicking, self).button_validate()
