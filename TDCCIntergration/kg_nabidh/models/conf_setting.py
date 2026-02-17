from odoo import fields, models, api
import requests


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    nabidh_login_url = fields.Char('NABIDH URL')
    sending_facility = fields.Char('Sending Facility', default="EMR")
    icd_code = fields.Char(' ICD code')


    @api.model
    def get_values(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res = super(ResConfigSettings, self).get_values()
        res.update(nabidh_login_url=get_param('kg_nabidh.nabidh_login_url'),
                   sending_facility=get_param('kg_nabidh.sending_facility'),
                   icd_code=get_param('kg_nabidh.icd_code'))
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('kg_nabidh.nabidh_login_url',
                  self.nabidh_login_url
                  )
        set_param('kg_nabidh.sending_facility',
                  self.sending_facility
                  )
        set_param('kg_nabidh.icd_code',
                  self.icd_code
                  )
        return res