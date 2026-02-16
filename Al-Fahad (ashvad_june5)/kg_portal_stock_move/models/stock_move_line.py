from odoo import fields, models


class ProductTemplateStock(models.Model):
    _inherit = 'stock.move.line'
    """inheriting stock move line model"""

    # warehouse_id= fields.Many2one('stock.warehouse',)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses',
                                     related='product_id.product_tmpl_id.warehouse_ids')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouses')
