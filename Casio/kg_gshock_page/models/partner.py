from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_cities(self, value):
        mapped_cities=[]
        cities = self.env['res.country.state'].sudo().search([('country_id.name', '=', value)])
        mapped_cities = cities.mapped('name')
        return list(mapped_cities)
