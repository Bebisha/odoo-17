# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models


class AssetRequestWizard(models.TransientModel):
    _name = 'wiz.asset.request'
    _description = 'Wiz Asset Request'

    date = fields.Date('Date', default=lambda d: fields.Date.today())
    emp_dept_id = fields.Reference(selection=[('hr.employee', 'Employee'),
                                              ('hr.department', 'Department')],
                                   string='Employee/Department')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    # @api.multi
    def assign_asset(self):
        """
        To set asset in employee assets and create line for assets history
        :return: True
        """
        self.ensure_one()
        asset_history = self.env['assets.history']
        emp_asset_obj = self.env['employee.assets']

        asset_rec = self.env[self._context.get('active_model')].browse(
            self._context.get('active_id'))
        # vals to create record for asset history
        vals = {
            'start_date': self.date,
            'asset_id': asset_rec.id
        }
        # vals to create record for employee held assets
        emp_ast_vals = {
            'receive_date': self.date,
            'asset_id': asset_rec.id,
            'employee_id': False,
        }
        if self.emp_dept_id._name == 'hr.employee':
            vals.update({'employee_id': self.emp_dept_id.id})
            asset_rec.employee_id = self.emp_dept_id.id
            emp_ast_vals['employee_id'] = self.emp_dept_id.id
        if self.emp_dept_id._name == 'hr.department':
            vals.update({'department_id': self.emp_dept_id.id})
            asset_rec.department_id = self.emp_dept_id.id
        asset_history.create(vals)
        emp_asset_obj.create(emp_ast_vals)
        asset_rec.asset_toggle = True
        return True
