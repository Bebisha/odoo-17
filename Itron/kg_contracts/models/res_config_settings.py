# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    approval_ids = fields.Many2many('res.users',string="Resource Approval", store=True,relation='res_approval_rel')
    contract_approval_ids = fields.Many2many('res.users',string="Contract Approval", store=True,relation='contract_approval_ids_rel',column1='settings_id',column2='user_id')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        approval_ids_str = params.get_param('approval_ids', default='')
        contract_approval_ids_str = params.get_param('contract_approval_ids', default='')
        approval_ids = []
        contract_approval_ids = []
        if approval_ids_str:
            approval_ids = [int(id.strip()) for id in approval_ids_str.strip('[]').split(',') if id.strip()]
        if contract_approval_ids_str:
            contract_approval_ids = [int(id.strip()) for id in contract_approval_ids_str.strip('[]').split(',') if id.strip()]
        res.update(
            approval_ids=approval_ids,
            contract_approval_ids=contract_approval_ids,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        approval_ids = self.approval_ids.ids if self.approval_ids else []
        approval_ids_str = ','.join(map(str, approval_ids))
        contract_approval_ids = self.contract_approval_ids.ids if self.contract_approval_ids else []
        contract_approval_ids_str = ','.join(map(str, contract_approval_ids))
        self.env['ir.config_parameter'].sudo().set_param("approval_ids", approval_ids_str)
        self.env['ir.config_parameter'].sudo().set_param("contract_approval_ids", contract_approval_ids_str)
