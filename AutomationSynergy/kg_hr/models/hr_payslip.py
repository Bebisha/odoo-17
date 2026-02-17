import calendar

from odoo import models, fields, api
from odoo.tools.safe_eval import datetime


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    current_month_days = fields.Float(compute='compute_current_dates', store=True)
    overtime_hours = fields.Float('Overtime Hrs', compute='compute_overtime_hrs')
    overtime_amount = fields.Float('Overtime Amount', compute='compute_total_overtime_amount')

    @api.depends('employee_id', 'overtime_hours', 'date_from', 'date_to')
    def compute_total_overtime_amount(self):
        for rec in self:
            rec.overtime_amount = False
            if  rec.overtime_hours>0:
                amount = (((rec.contract_id.wage * 30) / 365) / rec.overtime_hours) * rec.contract_id.ot_rate
                rec.overtime_amount = amount

    @api.depends('employee_id', 'date_from', 'date_to')
    def compute_overtime_hrs(self):
        for rec in self:
            rec.overtime_hours = False
            # rec.overtime_amount = False
            if rec.employee_id:
                overtime_hrs = self.env['hr.attendance'].search(
                    [('employee_id', '=', rec.employee_id.id)]).filtered(
                    lambda x: x.check_in.date() >= rec.date_from and x.check_out.date() <= rec.date_to)
                rec.overtime_hours = sum(overtime_hrs.mapped('ot_hours'))
            #     rec.overtime_amount = sum(overtime_hrs.mapped('ot_payment_new'))

    @api.depends('date_from')
    def compute_current_dates(self):
        for rec in self:
            current_date = rec.date_from
            rec.current_month_days = False
            if current_date:
                rec.current_month_days = calendar.monthrange(current_date.year, current_date.month)[1]

    def get_values_lines(self):
        for paysl in self:
            payslip = []
            basic = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'BASIC').mapped('total'))
            food_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'FA').mapped('total'))
            house_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'HRA').mapped('total'))
            travel_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'TA').mapped('total'))
            # advance_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'AA').mapped('total'))
            # bonus_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'BA').mapped('total'))
            # other_allowance = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'OTA').mapped('total'))
            overtime = paysl.overtime_hours * paysl.overtime_amount
            allowance = food_allowance + house_allowance + travel_allowance

            dnwd = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DNWD').mapped('total'))
            da = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DA').mapped('total'))
            dt = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DT').mapped('total'))
            dsd = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DSD').mapped('total'))
            # do = sum(paysl.line_ids.filtered(lambda x: x.salary_rule_id.code == 'DO').mapped('total'))
            gross = basic + allowance
            deductions = dnwd + da + dt + dsd
            net = gross + deductions
            values = {
                'basic': basic,
                'overtime': overtime,
                'food_allowance': food_allowance,
                'accommodation': house_allowance,
                'travel_allowance': travel_allowance,
                'gross': gross,
                'dnwd': dnwd,
                'deduction_advance': da,
                'telephone_deduction': dt,
                'deduction_security_deposit': dsd,
                'total_deduction': deductions,
                'net': net
            }
            return [values]
