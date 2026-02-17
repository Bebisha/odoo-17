from odoo import models, fields, api

class client_intake_form_config(models.TransientModel):
    _inherit='res.config.settings'

    edit_and_create = fields.Text(string='Terms and Condition')

    def set_values(self):
        res=super(client_intake_form_config,self).set_values()
        self.env['ir.config_parameter'].set_param('client_intake_form_config.edit_and_create',self.edit_and_create)
        return res

    @api.model
    def get_values(self):
        res = super(client_intake_form_config, self).get_values()
        ICPStudio = self.env['ir.config_parameter'].sudo()
        notes1 = ICPStudio.get_param('client_intake_form_config.edit_and_create')
        res.update(edit_and_create=notes1)
        return res

