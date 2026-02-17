from ast import literal_eval

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    daily_report_manager_ids = fields.Many2many('res.users', string="Daily Report Managers",
                                                relation='daily_report_rels',
                                                related="company_id.daily_report_manager_ids", readonly=False)

    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     params = self.env['ir.config_parameter'].sudo()
    #     daily_report_manager_ids = params.get_param('kg_crm_daily_report.daily_report_manager_ids', default=[])
    #     manager_ids = eval(daily_report_manager_ids) if daily_report_manager_ids else []
    #     res.update(
    #         daily_report_manager_ids=[(6, 0, manager_ids)],
    #     )
    #     return res
    #
    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     daily_report_manager_ids = self.daily_report_manager_ids.ids if self.daily_report_manager_ids else []
    #     self.env['ir.config_parameter'].sudo().set_param("kg_crm_daily_report.daily_report_manager_ids",
    #                                                      str(daily_report_manager_ids))
