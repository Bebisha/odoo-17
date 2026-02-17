# -*- coding: utf-8 -*-

from odoo import api, fields, models
import calendar
from datetime import date
from odoo.exceptions import UserError


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'hr.payslip'

    days_in_month = fields.Integer(string='Days in Month', compute='_compute_days_in_month')
    working_days = fields.Integer(compute='_compute_working_days')

    total_leave_days = fields.Integer(compute='_compute_leave_days')
    total_unpaid_leaves = fields.Integer(compute='_compute_unpaid_leaves')

    fixed_ot_allowance = fields.Float(string="Fixed OT Allowance", compute="compute_ot_allowance")
    total_ot_hours = fields.Float(string="Total OT Hours", compute="compute_ot_allowance")

    overseas_entries = fields.Float(string="Overseas")
    anchorage_entry = fields.Float(string="Anchorage")
    over_time = fields.Float(string="Overtime")
    over_time_rate = fields.Float(string="Fixed over time")

    air_ticket = fields.Float(string="Air Ticket", compute="compute_air_ticket")

    def compute_air_ticket(self):
        for rec in self:
            rec.air_ticket = 0.00
            total_ticket = 0
            overseas_lines = self.env['hr.deduction.line'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('date', '>=', rec.date_from),
                ('date', '<=', rec.date_to),
                ('state', '=', 'active')
            ])

            for line in overseas_lines:
                if line.deduction_id.allowance_rule_id.code == 'TIK' and line.deduction_id.state == 'approve':
                    total_ticket += line.amount
            rec.air_ticket = total_ticket

    def compute_ot_allowance(self):
        for rec in self:
            rec.fixed_ot_allowance = 0.00
            rec.total_ot_hours = 0.00
            if rec.date_from and rec.date_to and rec.employee_id:
                timesheet_ids = self.env['account.analytic.line'].search(
                    [('date', '>=', rec.date_from), ('date', '<=', rec.date_to),
                     ('employee_id', '=', rec.employee_id.id)])
                rec.total_ot_hours = sum(timesheet_ids.mapped('ot_hours')) if timesheet_ids else 0.00

                if rec.contract_id and rec.total_ot_hours != 0.00:
                    if rec.contract_id.ot_wage == 'monthly_fixed':
                        rec.fixed_ot_allowance = rec.contract_id.fixed_ot_allowance
                    elif rec.contract_id.ot_wage == 'hourly_fixed' and rec.contract_id.hourly_ot_allowance:
                        rec.fixed_ot_allowance = rec.contract_id.hourly_ot_allowance * rec.total_ot_hours

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_leave_days(self):
        for rec in self:
            if rec.employee_id and rec.date_from and rec.date_to:
                leaves = self.env['hr.leave'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('state', '=', 'validate'),
                    ('date_from', '>=', rec.date_from),
                    ('date_to', '<=', rec.date_to)
                ])
                rec.total_leave_days = sum(leaves.mapped('number_of_days'))
            else:
                rec.total_leave_days = 0

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_unpaid_leaves(self):
        for rec in self:
            if rec.employee_id and rec.date_from and rec.date_to:
                leaves = self.env['hr.leave'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('state', '=', 'validate'),
                    ('date_from', '>=', rec.date_from),
                    ('date_to', '<=', rec.date_to),
                    ('holiday_status_id', '=', self.env.ref('hr_holidays.holiday_status_unpaid').id)
                ])
                rec.total_unpaid_leaves = sum(leaves.mapped('number_of_days'))
            else:
                rec.total_unpaid_leaves = 0

    def _compute_working_days(self):
        for rec in self:
            if rec.date_from:
                cal = rec.employee_id.resource_calendar_id
                year = rec.date_from.year
                month = rec.date_from.month
                weekdays = set(int(att.dayofweek) for att in cal.attendance_ids)
                _, days_in_month = calendar.monthrange(year, month)

                count = 0
                for d in range(1, days_in_month + 1):
                    day = date(year, month, d)
                    if day.weekday() in weekdays:
                        count += 1
                rec.working_days = count
            else:
                rec.working_days = 0

    @api.depends('date_from')
    def _compute_days_in_month(self):
        for rec in self:
            if rec.date_from:
                year = rec.date_from.year
                month = rec.date_from.month
                rec.days_in_month = calendar.monthrange(year, month)[1]
            else:
                rec.days_in_month = 0

    @api.onchange('employee_id','date_from','date_to')
    def _onchange_employee_id(self):
        """ For reflecting the employee entries, salary pre-payments and delayed salaries in payslip """
        for payslip in self:
            payslip.input_line_ids = False
            payslip.anchorage_entry = 0.00
            payslip.overseas_entries = 0.00
            payslip.over_time = 0.00

            anchorage_entry = self.env['hr.employee.entry'].search(
                [('employee_id', '=', payslip.employee_id.id), ('start_date', '>=', payslip.date_from),
                 ('end_date', '<=', payslip.date_to), ('state', '=', 'approved'),
                 ('type_entry', '=', 'anchorage_entry')])
            overseas_entries = self.env['hr.employee.entry'].search(
                [('employee_id', '=', payslip.employee_id.id), ('start_date', '>=', payslip.date_from),
                 ('end_date', '<=', payslip.date_to), ('state', '=', 'approved'),
                 ('type_entry', '=', 'overseas_entries')])
            overtime = self.env['hr.employee.entry'].search(
                [('employee_id', '=', payslip.employee_id.id), ('start_date', '>=', payslip.date_from),
                 ('end_date', '<=', payslip.date_to), ('state', '=', 'approved'), ('type_entry', '=', 'overtime')])
            overtime_fixed_allowance = self.env['hr.employee.entry'].search(
                [('employee_id', '=', payslip.employee_id.id), ('start_date', '>=', payslip.date_from),
                 ('end_date', '<=', payslip.date_to), ('state', '=', 'approved'), ('type_entry', '=', 'overtime_fixed_allowance')])

            anchorage_entry = sum(anchorage_entry.mapped('anchorage_deduction'))
            overseas_entries = sum(overseas_entries.mapped('overseas_deduction'))
            overtime = sum(overtime.mapped('over_time'))
            over_time_rate = sum(overtime_fixed_allowance.mapped('over_time'))
            if anchorage_entry:
                val = {
                    'input_type_id': self.env.ref('kg_voyage_marine_hrms.anchorage_input_type').id,
                    'amount': anchorage_entry,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})
            if overseas_entries:
                val = {
                    'input_type_id': self.env.ref('kg_voyage_marine_hrms.overseas_input_type').id,
                    'amount': overseas_entries,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})
            if overtime:
                val = {
                    'input_type_id': self.env.ref('kg_voyage_marine_hrms.custom_overtime_input_type').id,
                    'amount': overtime,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})
            if over_time_rate:
                val = {
                    'input_type_id': self.env.ref('kg_voyage_marine_hrms.custom_overtime_fixed_input_type').id,
                    'amount': over_time_rate,
                    'contract_id': payslip.employee_id.contract_id.id,
                }
                payslip.write({'input_line_ids': [(0, 0, val)]})


            payslip.anchorage_entry = anchorage_entry
            payslip.overseas_entries = overseas_entries
            payslip.over_time = overtime
            payslip.over_time_rate = over_time_rate

    def action_print_payslip(self):
        """ Overridden to change payslip print """
        return self.env.ref('hr_payroll.action_report_payslip').report_action(self)

    def action_payslip_unpaid(self):
        return True

    def action_send_payslips_email(self):
        template = self.env.ref(
            'kg_voyage_marine_hrms.mail_template_payslip_employee',
            raise_if_not_found=False
        )
        print(template,"templatetemplatetemplate")
        if not template:
            raise UserError("Payslip mail template not found.")

        for slip in self:
            print(slip, "employee_id.work_email")
            if slip.state == 'done':
                continue
            if not slip.employee_id.work_email:
                continue
            print(slip,"employee_id.work_email")

            template.send_mail(
                slip.id,
                force_send=True,
                email_values={
                    'email_to': slip.employee_id.work_email,
                }
            )
            print(template,"template")
        # ✅ NO return


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_send_bach_payslips_email(self):
        template = self.env.ref(
            'kg_voyage_marine_hrms.mail_template_payslip_employee',
            raise_if_not_found=False
        )
        print(template, "templatetemplatetemplate")
        if not template:
            raise UserError("Payslip mail template not found.")

        for batch in self:
            print(batch, "batchbatchbatch")
            for slip in batch.slip_ids:
                print(slip, "employee_id.work_email")
                if slip.state == 'done':
                    continue
                if not slip.employee_id.work_email:
                    raise UserError(f"Employee {slip.employee_id.name} does not have a work email set.")
                    # continue
                print(slip, "employee_id.work_email")

                template.send_mail(
                    slip.id,
                    force_send=True,
                    email_values={
                        'email_to': slip.employee_id.work_email,
                    }
                )
                print(template, "template")



