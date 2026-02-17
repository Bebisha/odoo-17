# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KgHrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    _description = 'hr.leave.allocation'

    @api.constrains('holiday_status_id', 'employee_ids')
    def _annual_leave_allocation(self):
        """ Annual leave cannot be allocated for temporary employees"""
        for rec in self.employee_ids:
            if rec.contract_id.contract_type_id.code == 'Temporary' and self.holiday_status_id.annual_leave:
                raise ValidationError(f"Annual Leave cannot be allocated for temporary employee {rec.name}.")


class HRLeave(models.Model):
    _inherit = 'hr.leave'
    _description = 'hr.leave'

    balance_leave = fields.Float(string="Leave Balance", compute='_compute_leave_days')
    leave_total = fields.Float(string="Total Leaves", compute='_compute_leave_days')
    leaves_taken = fields.Float(string="Leaves Taken", compute='_compute_leave_days')
    contact_during_leave = fields.Char(string='Contact phone during leave')
    start_of_work = fields.Date(string='D.O. Start to work')

    @api.depends('employee_id','holiday_status_id')
    def _compute_leave_days(self):
        for rec in self:
            rec.balance_leave = False
            rec.leaves_taken = False
            rec.leave_total = False
            if rec.holiday_status_id:
                hr_leave_allocation_id = self.env['hr.leave.allocation'].search(
                    [('employee_id', '=', rec.employee_id.id),
                     ('holiday_status_id', '=', rec.holiday_status_id.id), ('state', '=', 'validate')])

                hr_leave_id = self.env['hr.leave'].search(
                    [('employee_id', '=', rec.employee_id.id), ('holiday_status_id', '=', rec.holiday_status_id.id),
                     ('state', '=', 'validate')])

                rec.leave_total = sum(hr_leave_allocation_id.mapped('number_of_days'))
                rec.balance_leave = rec.leave_total - sum(hr_leave_id.mapped('number_of_days'))
                rec.leaves_taken = rec.leave_total - rec.balance_leave
