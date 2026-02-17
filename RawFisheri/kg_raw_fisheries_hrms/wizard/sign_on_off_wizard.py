# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShopEntryWizard(models.TransientModel):
    _name = 'sign.on.off.wizard'
    _description = 'sign.on.off.wizard'

    employee_ids = fields.Many2many('hr.employee', string='Employees')
    sign_on = fields.Date(String='Sign On Date')
    sign_off = fields.Date(String='Sign Off Date')

    # def default_get(self, fields):
    #     """ Listing all crew members coming under logged in factory manager """
    #     res = super(ShopEntryWizard, self).default_get(fields)
    #     employees = self.env['hr.employee'].search(
    #         [('crew', '=', True), ('factory_manager_ids.user_id', '=', self.env.user.id)])
    #     res['employee_ids'] = [(6, 0, employees.ids)]
    #     return res

    def action_create_entries(self):
        """ Button action to create Sign On Off Entries """
        for employee in self.employee_ids:
            vals = {
                'employee_id': employee.id,
                'sign_on': self.sign_on,
                'sign_off': self.sign_off,
                'contract_reference': f"Contract : {employee.name or ''}"
            }
            self.env['sign.on.off'].create(vals)
