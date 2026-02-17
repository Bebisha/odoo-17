from odoo import api, fields, models


class KgCrmResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    margin = fields.Float(string='Margin %')
    hr_expense_alias_domain_id = fields.Char()

    @api.model
    def get_values(self):
        res = super(KgCrmResConfigSettings, self).get_values()
        margin = self.env['ir.config_parameter'].sudo().get_param('margin', default=False)
        res.update(
            margin=margin,
        )
        return res

    def set_values(self):
        super(KgCrmResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('margin', self.margin)
