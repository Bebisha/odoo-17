from odoo import models, fields, api

# class ResConfig(models.TransientModel):
#     _inherit = "res.config.settings"
#
#     notification_days = fields.Char(string="Subscription nofification days",
#                     config_parameter="sttl_sale_subscription.notification_duration", default=10)
#     remainder_mail_ids = fields.Char()
#     contract_app_ids = fields.Many2many('res.users', string="Contract Approval", store=True,
#                                              relation='contracts_approval_ids_rel', column1='setting_id',
#                                              column2='users_id')
#
#     notification_partner_ids = fields.Many2many('res.partner', string="Notification Recipient")
#
#     @api.model
#     def get_values(self):
#         get_param = self.env['ir.config_parameter'].sudo().get_param
#         res = super(ResConfig, self).get_values()
#         res.update(contract_app_ids=get_param('sttl_sale_subscription.contract_app_ids'),
#                 )
#         return res
#
#     # @api.multi
#     def set_values(self):
#         res = super(ResConfig, self).set_values()
#         set_param = self.env['ir.config_parameter'].sudo().set_param
#         set_param('sttl_sale_subscription.contract_app_ids',
#                   self.contract_app_ids
#                   )
#         return res



class ResCompany(models.Model):
    _inherit = "res.company"

    new_notification_users_ids = fields.Many2many(
        "hr.employee", 'ss_rel_new_notification_users_ids',
        string="Notification Users",
        check_company=True)


class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    conf_new_notification_users_ids = fields.Many2many(
        comodel_name='hr.employee',
        check_company=True,
        related='company_id.new_notification_users_ids',
        readonly=False
    )


