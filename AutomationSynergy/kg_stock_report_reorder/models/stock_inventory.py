# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductStockInherit(models.Model):
    _inherit = 'product.product'

    is_minimum_quantity = fields.Boolean(string="Is Reach Minimum Quantity", compute='action_check_reorder',
                                         default=False, store=True)

    # compute action for whether product reach minimum quantity
    @api.depends('is_minimum_quantity', 'name')
    def action_check_reorder(self):
        for rec in self:
            stock_rule = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', rec.id),
                                                                        ('product_min_qty', '=', rec.qty_available),
                                                                        ('qty_forecast', '=', rec.qty_available)])
            if stock_rule:
                rec.is_minimum_quantity = True
            else:
                rec.is_minimum_quantity = False

    # server action for pop-up
    def action_open_wizard_create_rfq(self):
        lines = []
        for rec in self.env.context.get('active_ids'):
            price = 0
            item_price = self.env['product.product'].search([('id', '=', rec)])
            if item_price:
                price = item_price.standard_price
            lines.append((0, 0, {
                'product_id': rec,
                'price': price
            }))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create RFQ'),
            'view_mode': 'form',
            'res_model': 'wizard.create.rfq',
            'target': 'new',
            'context': {'default_item_line_ids': lines}
        }
