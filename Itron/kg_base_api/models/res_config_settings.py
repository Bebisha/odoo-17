# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    report_users_ids = fields.Many2many('res.users',string="Attendance Report Users", store=True)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        report_users_ids_str = params.get_param('kg_base_api.report_users_ids', default=[])
        report_users_ids = eval(report_users_ids_str) if report_users_ids_str else []

        res.update(
            report_users_ids=[(6, 0, report_users_ids)],
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        report_users_ids = self.report_users_ids.ids if self.approval_ids else []
        self.env['ir.config_parameter'].sudo().set_param("kg_base_api.report_users_ids", str(report_users_ids))
