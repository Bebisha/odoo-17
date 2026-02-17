from odoo import models, fields, api


class KGHRContract(models.Model):
    _inherit = "hr.contract"

    hra_allowance = fields.Monetary(string="HRA Allowance")
    hra_deduction = fields.Monetary(string="HRA Deduction")
    food_allowance = fields.Monetary(string="Food Allowance")
    da_allowance = fields.Monetary(string="DA Allowance")
    telephone_allowance = fields.Monetary(string="Telephone Allowance")
    telephone_deduction = fields.Monetary(string="Telephone Deduction")
    special_allowance = fields.Monetary(string="Special Allowance")
    performance_allowance = fields.Monetary(string="Performance Allowance")
    transport_allowance = fields.Monetary(string="Transport Allowance")

    fixed_ot_allowance = fields.Monetary(string="Fixed OT Allowance")
    hourly_ot_allowance = fields.Monetary(string="Hourly OT Allowance")

    total_salary = fields.Monetary(string="Total Salary", compute='_compute_total_salary')

    per_day_salary = fields.Monetary(string="Day Salary", compute='compute_per_day_salary')
    hour_salary = fields.Monetary(string="Hour Salary", compute='compute_hour_salary')
    overseas_allowance = fields.Monetary(string="Overseas Rate")
    anchorage_allowance = fields.Monetary(string="Anchorage Rate")
    over_time = fields.Monetary(string="Overtime Rate")
    fixed_allowance = fields.Monetary(string="Fixed Allowance", default=100)
    is_ot_rate = fields.Boolean(default=True, copy=False)
    is_fixed_allowance = fields.Boolean(default=True, copy=False)

    ot_wage = fields.Selection(
        [('monthly_fixed', 'Monthly Fixed'), ('daily_fixed', 'Daily Fixed'), ('hourly_fixed', 'Hourly Fixed')],
        string="OT Wage")

    @api.depends(
        'wage', 'l10n_ae_housing_allowance', 'hra_deduction', 'food_allowance', 'da_allowance',
        'telephone_allowance', 'telephone_deduction', 'special_allowance',
        'performance_allowance', 'l10n_ae_transportation_allowance', 'fixed_ot_allowance',
        'hourly_ot_allowance', 'l10n_ae_other_allowances'
    )
    def _compute_total_salary(self):
        for record in self:
            total_allowances = (
                    record.wage +
                    record.l10n_ae_housing_allowance +
                    record.food_allowance +
                    record.da_allowance +
                    record.telephone_allowance +
                    record.special_allowance +
                    record.performance_allowance +
                    record.l10n_ae_transportation_allowance +
                    record.l10n_ae_other_allowances +
                    record.fixed_ot_allowance +
                    record.hourly_ot_allowance
            )

            total_deductions = (
                    record.hra_deduction +
                    record.telephone_deduction
            )

            record.total_salary = total_allowances - total_deductions

    def compute_per_day_salary(self):
        for rec in self:
            if rec.wage:
                rec.per_day_salary = (rec.wage) * (12 / 365)
            else:
                rec.per_day_salary = False

    def compute_hour_salary(self):
        for rec in self:
            if rec.per_day_salary:
                rec.hour_salary = rec.per_day_salary / 8
            else:
                rec.hour_salary = False
