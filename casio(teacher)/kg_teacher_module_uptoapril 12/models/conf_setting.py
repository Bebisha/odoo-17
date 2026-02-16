# -*- encoding: utf-8 -*-
from odoo import fields, models



class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sending_facility = fields.Many2many('res.partner', string="Administration/Education Business Marketing Team")

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        sending_facility = self.env['ir.config_parameter'].sudo().get_param('many2many.sending_facility')
        res.update({
            'sending_facility': [
                (6, 0, [int(x) for x in sending_facility.split(',')])] if sending_facility else False,
        })
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('many2many.sending_facility',
                                                         ','.join(map(str, self.sending_facility.ids)))
        return res