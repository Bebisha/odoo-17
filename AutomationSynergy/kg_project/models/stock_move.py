from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = "stock.move"

    material_id = fields.Many2one('material.purchase.requisition')
    @api.onchange('product_uom_qty', 'quantity')
    def _check_demanded_qty(self):
        for move in self:
            if move.sale_line_id:
                if move.quantity > move.product_uom_qty:
                    raise ValidationError(
                        'The demanded quantity cannot exceed the ordered quantity for product: %s' % move.product_id.name
                    )


class StockLocation(models.Model):
    _inherit = 'stock.location'

    is_project_virtual_location = fields.Boolean('Is Project virtual location', default=False)
    is_project_production_location = fields.Boolean('Is Project production location', default=False)


class StockMoveCustoms(models.Model):
    _inherit = 'stock.quant'
    _description = 'stock quant'

    @api.constrains('location_id')
    def check_location_id(self):
        for quant in self:
            if quant.location_id.usage == 'view':
                if quant.location_id.is_project_virtual_location:
                    pass
                else:
                    raise ValidationError(
                        _('You cannot take products from or deliver products to a location of type "view" (%s).',
                          quant.location_id.name))
