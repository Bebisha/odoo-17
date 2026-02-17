# -*- coding: utf-8 -*-
from odoo import models, api


class InventoryUpdates(models.Model):
    _inherit = 'inventory.update'

    @api.model
    def get_inventory_update_data(self):
        """ Function to load data for the inventory updates dashboard """
        result = []
        updates = self.search([])
        for update in updates:
            vessel = self.env['sponsor.sponsor'].sudo().search([('warehouse_id', '=', update.warehouse_id.id)])
            result.append({
                'product': update.product_id.name if update.product_id.name else None,
                'code': update.code if update.code else None,
                'batch_id': update.batch_id.name if update.batch_id.name else None,
                'date': update.date if update.date else None,
                'warehouse': update.warehouse_id.name if update.warehouse_id.name else None,
                'vessel': vessel.name if vessel.name else None,
                'onhand_qty': update.product_id.qty_available if update.product_id.qty_available else None,
                'daily_qty': update.quantity if update.quantity else None,
                'kilograms': update.kg if update.kg else None,
            })
        return result
