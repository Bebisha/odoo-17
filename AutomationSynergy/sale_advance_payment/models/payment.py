# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountPayment(models.Model):

    _inherit = "account.payment"

    sale_id = fields.Many2one('sale.order', "Sale", readonly=True,
                              states={'draft': [('readonly', False)]})
    payment_ref = fields.Char("Ref.")
    purchase_id = fields.Many2one('purchase.order', "Purchase", readonly=True,
                              states={'draft': [('readonly', False)]})
