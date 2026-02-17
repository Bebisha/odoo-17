# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, tools, api
_logger = logging.getLogger(__name__)



class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    late_approval_ids = fields.Many2many('res.users', string="Line Approval", store=True,
                                         relation='res_late_approval_ids')
    late_sec_approval_ids = fields.Many2many('res.users', string="Ceo Approval", store=True,
                                             relation='late_sec_approval_ids_rel', column1='settings_id',
                                             column2='user_id')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        late_approval_ids_str = params.get_param('late_approval_ids', default='')
        late_sec_approval_ids_str = params.get_param('late_sec_approval_ids', default='')

        late_approval_ids = [int(id.strip()) for id in late_approval_ids_str.strip('[]').split(',') if id.strip()]
        late_sec_approval_ids = [int(id.strip()) for id in late_sec_approval_ids_str.strip('[]').split(',') if
                                 id.strip()]

        res.update(
            late_approval_ids=[(6, 0, late_approval_ids)],
            late_sec_approval_ids=[(6, 0, late_sec_approval_ids)],
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        late_approval_ids_str = ','.join(
            map(str, self.late_approval_ids.ids)) if self.late_approval_ids else ''
        late_sec_approval_ids_str = ','.join(
            map(str, self.late_sec_approval_ids.ids)) if self.late_sec_approval_ids else ''

        self.env['ir.config_parameter'].sudo().set_param("late_approval_ids", late_approval_ids_str)
        self.env['ir.config_parameter'].sudo().set_param("late_sec_approval_ids", late_sec_approval_ids_str)


# class ResUsersCustom(models.Model):
#     _inherit = 'res.users'
#
#     def _action_reset_password(self, _logger=None):
#         for user in self:
#             # Override email_from after calling the parent method
#             super(ResUsersCustom, self)._action_reset_password()
#             # Search for the mail created and update email_from
#
#             mail = self.env['mail.mail'].search([('email_to', '=', user.email)], order='create_date desc', limit=1)
#             print(mail,"frff")
#             if mail:
#                 mail.email_from = 'itron@klystronglobal.com'
#                 print(mail.email_from,"jkfkuy")
#                 mail.sudo().send()
        # _logger.info("Password reset email sent for user <%s> with overridden email_from", self.mapped('login'))
