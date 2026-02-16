# -*- coding: utf-8 -*-

from odoo import fields, models, api

class EmployeeLeaveReport(models.Model):
    _name = 'employee.leave.report'
    _description = 'Employee Leave Report'

    name = fields.Many2one('hr.employee', string='Employee', required=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type', required=True)
    total_leave_allocation = fields.Float(string='Total Leave Allocation')

    total_leave_taken = fields.Float(string='Total Leave Taken', compute='_compute_total_leave_taken')
    leave_remaining = fields.Float(string='Leave Remaining', compute='_compute_leave_remaining')
    leave_ids = fields.One2many('hr.leave', 'employee_leave_report_id', string='Leave Records')

    @api.depends('total_leave_allocation', 'leave_ids.state')
    def _compute_leave_remaining(self):
        for record in self:
            total_leave_taken = sum(record.leave_ids.filtered(lambda leave: leave.state == 'validate').mapped('number_of_days'))
            record.leave_remaining = record.total_leave_allocation - total_leave_taken

    @api.depends('name', 'leave_ids.state')
    def _compute_total_leave_taken(self):
        for record in self:
            total_leave_taken = sum(record.leave_ids.filtered(lambda leave: leave.state == 'validate').mapped('number_of_days'))
            record.total_leave_taken = total_leave_taken

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    employee_leave_report_id = fields.Many2one('employee.leave.report', string='Employee Leave Report')



