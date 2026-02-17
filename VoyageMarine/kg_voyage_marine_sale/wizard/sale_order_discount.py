from odoo import models, fields, api,Command,_

class SaleOrderDiscountInherit(models.TransientModel):
    _inherit = 'sale.order.discount'

    def _prepare_discount_line_values(self, product, amount, taxes, description=None):
        self.ensure_one()

        vals = {
            'order_id': self.sale_order_id.id,
            'product_id': product.id,
            'sequence': 999,
            'price_unit': -amount,
            'fixed_discount':-amount,
            'tax_id': [Command.set(taxes.ids)],
        }
        if description:
            # If not given, name will fallback on the standard SOL logic (cf. _compute_name)
            vals['name'] = description

        return vals

    def _prepare_discount_product_values(self):
        self.ensure_one()
        return {
            'name': _('Discount'),
            'type': 'service',
            'invoice_policy': 'order',
            'list_price': 0.0,
            'is_discount_product':True,
            'company_id': self.company_id.id,
            'taxes_id': None,
        }

    def action_apply_discount(self):
        self.ensure_one()
        self = self.with_company(self.company_id)
        if self.discount_type == 'sol_discount':
            self.sale_order_id.order_line.write({'discount': self.discount_percentage*100})
            self.sale_order_id.order_line._onchange_discount()
        else:
            self._create_discount_lines()
            self.sale_order_id.order_line._onchange_discount()
            self.sale_order_id.order_line._onchange_discount()