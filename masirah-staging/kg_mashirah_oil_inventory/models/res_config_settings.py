from ast import literal_eval

from odoo import models, fields, api
from odoo.tools import str2bool


class MaterialConsumptionConfiguring(models.TransientModel):
    _inherit = 'res.config.settings'

    destination_location = fields.Many2one('stock.location', string="Destination Location")

    def set_values(self):
        res = super(MaterialConsumptionConfiguring, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('kg_mashirah_oil_manufacturing.destination_location',
                                                         self.destination_location.id)
        return res


    @api.model
    def get_values(self):
        sup = super(MaterialConsumptionConfiguring, self).get_values()
        destination_location = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_manufacturing.destination_location', default=False)
        if destination_location:
            sup.update(destination_location=int(destination_location))
        return sup
