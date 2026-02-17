# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    approval_ids = fields.Many2many('res.users', string="Resource Approval", relation='res_approval_rel')
    contract_approval_ids = fields.Many2many('res.users', string="Contract Approval", relation='con_approval_rel')
    second_approval_ids = fields.Many2many('res.users', string="Second Approval", relation='second_approval_rel')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        approval_ids_str = params.get_param('project_task_analysis.approval_ids', default=[])
        contract_approval_ids_str = params.get_param('project_task_analysis.contract_approval_ids', default=[])
        second_approval_ids_str = params.get_param('project_task_analysis.second_approval_ids', default=[])

        approval_ids = eval(approval_ids_str) if approval_ids_str else []
        contract_approval_ids = eval(contract_approval_ids_str) if contract_approval_ids_str else []
        second_approval_ids = eval(second_approval_ids_str) if second_approval_ids_str else []

        res.update(
            approval_ids=[(6, 0, approval_ids)],
            contract_approval_ids=[(6, 0, contract_approval_ids)],
            second_approval_ids=[(6, 0, second_approval_ids)],
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()

        approval_ids = self.approval_ids.ids if self.approval_ids else []
        contract_approval_ids = self.contract_approval_ids.ids if self.contract_approval_ids else []
        second_approval_ids = self.second_approval_ids.ids if self.second_approval_ids else []

        self.env['ir.config_parameter'].sudo().set_param("project_task_analysis.approval_ids", str(approval_ids))
        self.env['ir.config_parameter'].sudo().set_param("project_task_analysis.contract_approval_ids", str(contract_approval_ids))
        self.env['ir.config_parameter'].sudo().set_param("project_task_analysis.second_approval_ids", str(second_approval_ids))

