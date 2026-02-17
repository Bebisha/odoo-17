from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    crm_team_id = fields.Many2one('crm.team', string='CRM Team',config_parameter='customer_data_api.crm_team_id')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        crm_team_id = params.get_param('crm_team_id', default=False)
        res.update(
            crm_team_id=int(crm_team_id),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("crm_team_id", self.crm_team_id.id)