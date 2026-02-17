from ast import literal_eval

from odoo import models,fields,api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    api_key = fields.Char('Api Key',default="api")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('kg_push_notification.api_key', self.api_key)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        with_user = self.env['ir.config_parameter'].sudo()
        api_key = with_user.get_param('kg_push_notification.api_key')
        res.update(api_key=api_key)
        return res