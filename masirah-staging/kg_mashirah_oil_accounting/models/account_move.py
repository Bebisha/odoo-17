from odoo import models
from odoo.exceptions import ValidationError


class KGAccountMoveInherit(models.Model):
    _inherit = "account.move"

    def action_post(self):
        if self.move_type == 'in_invoice' and self.invoice_origin:
            po_id = self.env['purchase.order'].search([('name', '=', self.invoice_origin)])
            if po_id:
                po_value = sum(po_id.mapped('amount_in_currency'))
                if po_value < abs(self.amount_total_signed):
                    raise ValidationError(
                        "Bill Amount cannot be exceed the Purchase Amount.\n\t Purchase Amount is %.2f %s." % (
                            po_value, self.company_currency_id.name))
        return super(KGAccountMoveInherit, self).action_post()
