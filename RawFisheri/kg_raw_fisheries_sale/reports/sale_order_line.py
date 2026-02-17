# -- coding: utf-8 --

from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    date_order = fields.Datetime(string='Order Date', related='order_id.date_order', store=True)

    def load_price_history_details(self):
        """ Function to load data in the pivot view """
        sale_orders = self.env['sale.order'].sudo().search([('state', '=', 'sale')], order='date_order desc')

        domain_list = []
        for order in sale_orders:
            for line in order.order_line:
                domain_list.append(line.id)
        return {
            'name': _('Sale Price History Report'),
            'view_type': 'form',
            'view_mode': 'pivot,tree',
            'domain': [('id', 'in', domain_list)],
            'context': {
                'search_default_groupby_vessel_id': 1,
                'search_default_groupby_product_id': 1,
                'search_default_groupby_date_order:month': 1
            },
            'res_model': 'sale.order.line',
            'type': 'ir.actions.act_window',
            'target': 'main',
        }
