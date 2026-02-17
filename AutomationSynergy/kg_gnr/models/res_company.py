from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    is_default_picking = fields.Boolean( string="Picking")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_type = fields.Selection(
        [('local_purchase', 'Local Purchase'), ('meast', 'Middle east'), ('international', 'International'),
         ('sisconcern', 'Sister Concern'), ], string='Purchase Type', default="local_purchase",
        )
