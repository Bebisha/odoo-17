from odoo import fields, models, api


class KGStockMoveInherit(models.Model):
    _inherit = 'stock.move'

    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel", related="location_dest_id.vessel_id", store=True)
    kilograms = fields.Float(string='Kilograms', compute='compute_qty_in_kg')
    is_non_sale_location = fields.Boolean(default=False, string="Is Non-Sale Location",
                                          related="warehouse_id.is_non_sale_location", store=True)

    @api.depends('quantity', 'product_uom')
    def compute_qty_in_kg(self):
        for update in self:
            ref_qty = update.product_uom.factor_inv
            update.write({
                'kilograms': update.quantity * ref_qty
            })

    @api.model
    def create(self, vals):
        res = super(KGStockMoveInherit, self).create(vals)
        if res and not res.stock_date:
            res.stock_date = fields.Date.today()
        return res
