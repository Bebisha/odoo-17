# -*- coding: utf-8 -*-


from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mr_id = fields.Many2one('material.purchase.requisition', 'Material Request')

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_material_issue = fields.Boolean(string="Material Issue")

class StockMove(models.Model):
    _inherit = 'stock.move'

    mr_line_id = fields.Many2one('requisition.line', 'Material Requisition Line')


