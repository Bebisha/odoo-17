# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_approved = fields.Boolean(copy=False, default=False)

    def action_approve(self):
        self.is_approved = True
