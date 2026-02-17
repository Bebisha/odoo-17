from ast import literal_eval

from odoo import fields, models,_,api
from odoo.exceptions import ValidationError, UserError


class ResTimeoffConfigInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    general_manager_ids = fields.Many2many('res.users', 'timeoff_general_manager', string='GM')
    hr_expense_alias_domain_id = fields.Char()

    def set_values(self):
        res = super(ResTimeoffConfigInherit, self).set_values()

        self.env['ir.config_parameter'].sudo().set_param('kg_timeoff.general_manager_ids',
                                                         self.general_manager_ids.ids)




        return res

    def get_values(self):

        sup = super(ResTimeoffConfigInherit, self).get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        general_manager = with_user.get_param('kg_timeoff.general_manager_ids')

        sup.update(
                   general_manager_ids=[(6, 0, literal_eval(general_manager))] if general_manager else [],
                   )

        return sup

