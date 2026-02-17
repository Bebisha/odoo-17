from odoo import models, fields, api, _, SUPERUSER_ID


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    stock_date = fields.Date(string='Inventory Date')
    batch_id = fields.Many2one("stock.batch", string="Batch")

    user_id = fields.Many2one(
        'res.users', 'Assigned To', help="User assigned to do product count.")
    user_ids = fields.Many2many("res.users", string="Vessel Users")

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, package_id=False, package_dest_id=False):
        res = super()._get_inventory_move_values(qty, location_id, location_dest_id, package_id,
                                                 package_dest_id)
        if res.get('move_line_ids'):
            res['move_line_ids'][0][2].update({
                'stock_date': self.stock_date,
                'batch_id': self.batch_id.id,
            })
        res['stock_date'] = self.stock_date
        res['warehouse_id'] = self.warehouse_id.id
        return res
