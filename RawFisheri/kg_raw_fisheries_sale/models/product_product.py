# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_product_multiline_description_sale(self):
        """ Overriden to change product description to name from display_name """
        name = self.name
        if self.description_sale:
            name += '\n' + self.description_sale

        return name


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_view_price_history(self):
        """ Function to load price history of products """

        sale_orders_lines = self.env['sale.order.line'].sudo().search(
            [('product_template_id', '=', self.id), ('order_id.state', '=', 'sale')], order='date_order desc')

        domain_list = sale_orders_lines.mapped('id')
        return {
            'name': _('Price History'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'pivot,tree',
            'domain': [('id', 'in', domain_list)],
            'context': {
                'search_default_groupby_vessel_id': 1,
                'search_default_groupby_product_id': 1,
                'search_default_groupby_date_order:month': 1
            },
        }
