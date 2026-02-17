from ast import literal_eval

from odoo import models,fields,api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    per_weak_cost = fields.Float(string="Per Weak Cost")
    crm_daily_mail_users_ids = fields.Many2many('res.users', string="Leads Daily Mail users", store=True,
                                         relation='res_crm_daily_mail_users_ids')

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        crm_daily_mail_users_ids_str = ','.join(
            map(str, self.crm_daily_mail_users_ids.ids)) if self.crm_daily_mail_users_ids else ''
        self.env['ir.config_parameter'].sudo().set_param("crm_daily_mail_users_ids", crm_daily_mail_users_ids_str)

        self.env['ir.config_parameter'].sudo().set_param('kg_crm.per_weak_cost', self.per_weak_cost)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()


        with_user = self.env['ir.config_parameter'].sudo()
        crm_daily_mail_users_ids_str = with_user.get_param('crm_daily_mail_users_ids', default='')
        crm_daily_mail_users_ids = [int(id.strip()) for id in crm_daily_mail_users_ids_str.strip('[]').split(',') if id.strip()]


        per_weak_cost = with_user.get_param('kg_crm.per_weak_cost')
        res.update(per_weak_cost=per_weak_cost,
        crm_daily_mail_users_ids = [(6, 0, crm_daily_mail_users_ids)],
        )
        return res