from odoo import models, fields


class ServiceProductLine(models.Model):
    _name = "service.product.line"
    _description = "Service Products"

    name = fields.Char(string="Reference")
    so_line_id = fields.Many2one("sale.order.line", string="SO Lines")
    so_id = fields.Many2one("sale.order", string="SO")
    product_id = fields.Many2one("product.product", string="Product")
    description = fields.Char(string="Description")
    qty = fields.Float(string="Quantity")
    uom_id = fields.Many2one("uom.uom", string="UOM")
    picking_id = fields.Many2one("stock.picking", string="Transfer")
