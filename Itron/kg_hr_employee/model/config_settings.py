# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    remainder_mail_ids = fields.Many2many('res.users', string="HR Manager", relation='res_approval_rel_rem')


    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        remainder_ids_str = params.get_param('kg_hr_employee.remainder_mail_ids', default=[])

        remainder_ids = eval(remainder_ids_str) if remainder_ids_str else []

        res.update(
            remainder_mail_ids=[(6, 0, remainder_ids)],
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()

        remainder_ids = self.remainder_mail_ids.ids if self.remainder_mail_ids else []

        self.env['ir.config_parameter'].sudo().set_param("kg_hr_employee.remainder_mail_ids", str(remainder_ids))


