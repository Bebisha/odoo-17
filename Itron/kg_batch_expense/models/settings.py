# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    expense_approval_ids = fields.Many2many('res.users', string="Expense First Approval", store=True,
                                            relation='res_expense_approval_ids')
    expense_sec_approval_ids = fields.Many2many('res.users', string="Expense Second Approval", store=True,
                                                relation='expense_sec_approval_ids_rel', column1='settings_id',
                                                column2='user_id')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        expense_approval_ids_str = params.get_param('expense_approval_ids', default='')
        expense_sec_approval_ids_str = params.get_param('expense_sec_approval_ids', default='')

        expense_approval_ids = [int(id.strip()) for id in expense_approval_ids_str.strip('[]').split(',') if id.strip()]
        expense_sec_approval_ids = [int(id.strip()) for id in expense_sec_approval_ids_str.strip('[]').split(',') if
                                    id.strip()]

        res.update(
            expense_approval_ids=[(6, 0, expense_approval_ids)],
            expense_sec_approval_ids=[(6, 0, expense_sec_approval_ids)],
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        expense_approval_ids_str = ','.join(
            map(str, self.expense_approval_ids.ids)) if self.expense_approval_ids else ''
        expense_sec_approval_ids_str = ','.join(
            map(str, self.expense_sec_approval_ids.ids)) if self.expense_sec_approval_ids else ''

        self.env['ir.config_parameter'].sudo().set_param("expense_approval_ids", expense_approval_ids_str)
        self.env['ir.config_parameter'].sudo().set_param("expense_sec_approval_ids", expense_sec_approval_ids_str)
