# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class DischargeEntryWizard(models.TransientModel):
    _name = 'discharge.entry.wizard'
    _description = 'discharge.entry.wizard'

    employee_ids = fields.Many2many('hr.employee', string='Employees')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    date = fields.Date(String='Date')
    start_date = fields.Date(string="Start Date", required=True)

    def default_get(self, fields):
        """ Listing all crew members coming under logged in factory manager """
        res = super(DischargeEntryWizard, self).default_get(fields)
        employees = self.env['hr.employee'].search(
            [('crew', '=', True), ('factory_manager_ids.user_id', '=', self.env.user.id)])
        res['employee_ids'] = [(6, 0, employees.ids)]
        return res

    def action_create_entries(self):
        """ Button action to create Discharge Entries """
        # entries = self.env['hr.employee.entry'].search(
        #     [('start_date', '<=', self.start_date), ('end_date', '>=', self.start_date)])
        # if not entries:
        for employee in self.employee_ids:
            vals = {
                'employee_id': employee.id,
                'date': self.date,
                'start_date': self.start_date,
            }
            self.env['hr.discharge'].create(vals)

    def action_create_from_employee_entries(self):
        """ Button Action To Create Shop Entries From Employee Entries """

        first_day = self.date.replace(day=1)
        last_day = first_day + relativedelta(day=31)

        if self.vessel_id:
            employees = self.env['hr.employee.entry'].search([
                ('vessels_id', '=', self.vessel_id.id),
                ('start_date', '<=', last_day),
                ('end_date', '>=', first_day)
            ]).mapped('employee_id')
        else:
            employees = self.env['hr.employee.entry'].search([
                ('start_date', '<=', last_day),
                ('end_date', '>=', first_day)
            ]).mapped('employee_id')

        for employee in employees:
            vals = {
                'employee_id': employee.id,
                'date': self.date
            }
            self.env['hr.discharge'].create(vals)
