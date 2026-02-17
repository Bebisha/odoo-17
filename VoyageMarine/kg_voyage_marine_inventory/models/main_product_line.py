from odoo import fields, models


class MainProductLines(models.Model):
    _name = 'main.product.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Main Products Lines"

    name = fields.Char()
    picking_id = fields.Many2one('stock.picking')
    product_id = fields.Many2one("product.product", string="Product")
    description = fields.Text(string='Description', store=True)
    quantity = fields.Float(string='Qty', default=1)
    uom_id = fields.Many2one('uom.uom', string='UOM')
    boe_id = fields.Many2one("mrp.bom", string="BOE")
    remarks = fields.Text(string="Remarks")

