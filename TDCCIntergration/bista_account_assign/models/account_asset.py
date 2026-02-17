# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'

    department_id = fields.Many2one('hr.department', string='Department')
    recovery_amount = fields.Float('Recovery Amount')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    asset_history_ids = fields.One2many('assets.history', 'asset_id')
    asset_toggle = fields.Boolean(string="Asset Toggle")

    # @api.multi
    # def set_assign_realise(self):
    #     '''
    #     To set assign and release assets to Employee or Department
    #     :return: wizard
    #     '''
    #     if self.asset_toggle:
    #         history_ids = self.asset_history_ids.sorted(
    #             lambda x: x.id, reverse=True)
    #         if history_ids:
    #             history_ids[0].write({'end_date': fields.Date.today()})
    #             self.asset_toggle = False
    #         if self.employee_id.employee_asset_ids:
    #             asset_line = self.employee_id.employee_asset_ids.sorted(
    #                 lambda x: x.id, reverse=True).filtered(
    #                 lambda x: x.asset_id.id == self.id)
    #             asset_line[0].recover_date = fields.Date.today()
    #         self.department_id = self.employee_id = False
    #         return True
    #     view_id = self.env.ref('bista_account_assign.wiz_view_asset_req')
    #     return {
    #         'name': 'Assign Request',
    #         'type': 'ir.actions.act_window',
    #         'view_id': view_id.id,
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'wiz.asset.request',
    #         'target': 'new',
    #     }
    def set_assign_realise(self):
        '''
        To set assign and release assets to Employee or Department
        :return: wizard
        '''
        if self.asset_toggle:
            history_ids = self.env['asset.history'].search([('asset_id', '=', self.id)], order='id desc', limit=1)
            if history_ids:
                history_ids.write({'end_date': fields.Date.today()})
                self.asset_toggle = False
            if self.employee_id.employee_asset_ids:
                asset_line = self.env['employee.asset'].search(
                    [('asset_id', '=', self.id), ('employee_id', '=', self.employee_id.id)], order='id desc', limit=1)
                if asset_line:
                    asset_line.recover_date = fields.Date.today()
            self.department_id = self.employee_id = False
            return True
        view_id = self.env.ref('bista_account_assign.wiz_view_asset_req').id
        return {
            'name': 'Assign Request',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'view_mode': 'form',
            'res_model': 'wiz.asset.request',
            'target': 'new',
        }

class AssetsHistory(models.Model):
    _name = 'assets.history'
    _description = "Asset History"

    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one('hr.department', "Department")
    asset_id = fields.Many2one('account.asset.asset', string="Asset")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)


class EmployeeAssets(models.Model):
    _name = 'employee.assets'
    _description = "Employee Assets"

    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    receive_date = fields.Date('Receive Date')
    recover_date = fields.Date('Recover Date')
    employee_id = fields.Many2one('hr.employee',
                                  string='Employee')
    department_id = fields.Many2one("hr.department", string='Department')
    penalties = fields.Float(string="Penalties")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)


class Employee(models.Model):
    _inherit = 'hr.employee'

    employee_asset_ids = fields.One2many('employee.assets', 'employee_id',
                                         string="Assets")
