
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from odoo.tools.populate import compute
import warnings

class KGSaleOrder(models.Model):
    _inherit = "stock.location"

    is_service_location = fields.Boolean(defalt=False,copy=False)
    is_empty = fields.Boolean(
        string='Free / Empty',
        compute='_compute_is_empty',
        store=True
    )

    @api.depends('quant_ids.quantity')
    def _compute_is_empty(self):
        for location in self:
            internal_quants = location.quant_ids.filtered(
                lambda q: q.location_id.usage == 'internal'
            )
            total_qty = sum(internal_quants.mapped('quantity'))
            location.is_empty = total_qty <= 0
