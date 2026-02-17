from odoo import api, fields, models, tools, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    destination_location_id = fields.Many2one('stock.location', string="Destination Location")
