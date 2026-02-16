from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    bom_id = fields.Many2one('mrp.bom', string='Bill of Materials')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and self.bom_id:
            # Check if there's already a BoM line for this product in the BoM
            existing_bom_line = self.env['mrp.bom.line'].search([
                ('bom_id', '=', self.bom_id.id),
                ('product_id', '=', self.product_id.id)
            ], limit=1)

            # If no BoM line exists for this product, create a new one
            if not existing_bom_line:
                bom_line_values = {
                    'bom_id': self.bom_id.id,
                    'product_id': self.product_id.id,
                    'product_qty': 1,  # You can set the quantity as needed
                }
                self.env['mrp.bom.line'].create(bom_line_values)




class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    bom_id = fields.Many2one('mrp.bom', string='Bill of Materials')

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        if self.sale_order_id:
            self.bom_id = self.sale_order_id.order_line.bom_id.id

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            bom = self.env['mrp.bom'].sudo().search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)], limit=1)
            self.bom_id = bom.id if bom else False
