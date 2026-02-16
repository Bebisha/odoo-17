from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    manager_id = fields.Many2one("hr.employee")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('kg_mashirah_oil_hrms.manager_id',
                                                         self.manager_id.id)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        manager_id = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_hrms.manager_id', default=False)
        if manager_id:
            res.update(manager_id=int(manager_id))
        return res