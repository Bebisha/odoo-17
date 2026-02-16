# -*- encoding: utf-8 -*-

from odoo import models, fields, api,_

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_create_purchase_order(self):
        view_id = self.env.ref('kg_sale_to_purchase.view_create_purchase_wizard').id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'create.purchase.wizard',
            'view_id': view_id,
            'target': 'new',
            'context': {'default_sale_order_id': self.id},
        }

    def action_view_related_purchase_orders(self):
        related_purchase_orders = self.env['purchase.order'].search([('sale_order_id', '=', self.id)])

        action = {
            'name': _('Sale to Purchase'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'target': 'current',
            'domain': [('id', 'in', related_purchase_orders.ids)],
        }

        return action

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
