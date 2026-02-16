from odoo import models, fields, api


class RevisedPurchaseOrderLine(models.Model):
    _name = 'poline.revised'
    _rec_name = 'line_custom_id'
    _description = 'Revised Purchase Order Line'

    line_custom_id = fields.Many2one(
        'po.revised',
        string='Revised Line',
    )

    product_id_rev = fields.Many2one(
        'product.product',
        string='Product',
    )

    name_rev = fields.Char(
        string='Description',
    )
    qty_rev = fields.Char(
        string='Ordered Quantity',
    )
    uom_rev = fields.Many2one(
        #        'product.uom',
        'uom.uom',
        string='Unit of Measure',
    )
    price_rev = fields.Float(
        string='Price Unit',
    )
    subtotal_rev = fields.Float(
        string='Subtotal',
    )
    total_rev = fields.Float(
        string='Total',
    )
    currency_id = fields.Many2one(
        "res.currency",
        related='line_custom_id.purchase_order_id.order_line.currency_id',
        string="Currency",
        store=True,
    )
    sale_person_line_id = fields.Many2one(
        'res.users',
        string='Sales Person',
        related='line_custom_id.purchase_order_id.user_id',
        store=True,
    )