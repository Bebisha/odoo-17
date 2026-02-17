# -*- coding: utf-8 -*-
from ast import literal_eval

from odoo import fields, models, _, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hr_id = fields.Many2one('hr.employee')
    finance_id = fields.Many2one('hr.employee')
    ceo_id = fields.Many2one('hr.employee')
    purchase_manager_ids = fields.Many2many('res.users', 'po_finance_rel', string='Purchase Manager')
    general_manager_ids = fields.Many2many('res.users', 'po_operations_rel', string='GM')
    finance_manager_ids = fields.Many2many('res.users', 'po_finance_manager_rel', string='Finance Manager')
    line_manager_ids = fields.Many2many('res.users', 'line_manager_rel', string='Line Manager')
    department_manager_ids = fields.Many2many('res.users', 'department_manager_rel', string='Department Manager')
    hr_manager_ids = fields.Many2many('res.users', 'hr_manager_rel', string='HR Manager')

    # def get_values(self):
    #     sup = super(ResConfigSettings, self).get_values()
    #     with_user = self.env['ir.config_parameter'].sudo()
    #     purchase_manager = with_user.get_param('kg_hr.purchase_manager_ids')
    #     general_manager = with_user.get_param('kg_hr.general_manager_ids')
    #     finance_manager = with_user.get_param('kg_hr.finance_manager_ids')
    #     line_manager = with_user.get_param('kg_hr.line_manager_ids')
    #     department_manager = with_user.get_param('kg_hr.department_manager_ids')
    #     hr_manager = with_user.get_param('kg_hr.hr_manager_ids')
    #
    #     sup.update(purchase_manager_ids=[(6, 0, literal_eval(purchase_manager))] if purchase_manager else [],
    #                general_manager_ids=[(6, 0, literal_eval(general_manager))] if general_manager else [],
    #                finance_manager_ids=[(6, 0, literal_eval(finance_manager))] if finance_manager else [],
    #                line_manager_ids=[(6, 0, literal_eval(line_manager))] if line_manager else [],
    #                department_manager_ids=[(6, 0, literal_eval(department_manager))] if department_manager else [],
    #                hr_manager_ids=[(6, 0, literal_eval(hr_manager))] if hr_manager else [],
    #                )
    #     return sup

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('kg_hr.hr_id',
                                                         self.hr_id.id)
        self.env['ir.config_parameter'].sudo().set_param('kg_hr.finance_id',
                                                         self.finance_id.id)
        self.env['ir.config_parameter'].sudo().set_param('kg_hr.ceo_id',
                                                         self.ceo_id.id)
        self.env['ir.config_parameter'].sudo().set_param('kg_hr.purchase_manager_ids',
                                                         self.purchase_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_hr.general_manager_ids',
                                                         self.general_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_hr.finance_manager_ids',
                                                         self.finance_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_hr.line_manager_ids',
                                                         self.line_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_hr.department_manager_ids',
                                                         self.department_manager_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('kg_hr.hr_manager_ids',
                                                         self.hr_manager_ids.ids)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        hr_id = self.env['ir.config_parameter'].sudo().get_param(
            'kg_hr.hr_id', default=False)
        finance_id = self.env['ir.config_parameter'].sudo().get_param(
            'kg_hr.finance_id', default=False)
        ceo_id = self.env['ir.config_parameter'].sudo().get_param(
            'kg_hr.ceo_id', default=False)
        with_user = self.env['ir.config_parameter'].sudo()
        purchase_manager = with_user.get_param('kg_hr.purchase_manager_ids')
        general_manager = with_user.get_param('kg_hr.general_manager_ids')
        finance_manager = with_user.get_param('kg_hr.finance_manager_ids')
        line_manager = with_user.get_param('kg_hr.line_manager_ids')
        department_manager = with_user.get_param('kg_hr.department_manager_ids')
        hr_manager = with_user.get_param('kg_hr.hr_manager_ids')

        res.update(purchase_manager_ids=[(6, 0, literal_eval(purchase_manager))] if purchase_manager else [],
                   general_manager_ids=[(6, 0, literal_eval(general_manager))] if general_manager else [],
                   finance_manager_ids=[(6, 0, literal_eval(finance_manager))] if finance_manager else [],
                   line_manager_ids=[(6, 0, literal_eval(line_manager))] if line_manager else [],
                   department_manager_ids=[(6, 0, literal_eval(department_manager))] if department_manager else [],
                   hr_manager_ids=[(6, 0, literal_eval(hr_manager))] if hr_manager else [],
                   hr_id=int(hr_id) if hr_id else False,
                   finance_id=int(finance_id) if finance_id else False,
                   ceo_id=int(ceo_id) if ceo_id else False,
                   )

        return res
