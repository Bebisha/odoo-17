from odoo import models, fields


class KGStockLocationInherit(models.Model):
    _inherit = "stock.location"

    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel", related="warehouse_id.vessel_id", store=True)
