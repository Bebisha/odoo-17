# -*- coding: utf-8 -*-
import calendar
from datetime import date, datetime
from odoo import api, fields, models


class KgSalesTarget(models.Model):
    _name = "kg.sales.target"
    _rec_name = "user_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Kg Sales Target"
    _order = 'user_id desc'

    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        required=True,
        domain="[('is_salesperson', '=', True)]"
    )
    tot_per = fields.Float("Allocated (%) ", compute="_compute_total")
    annual_target_amount = fields.Monetary("Annual Target", compute="_compute_total")
    achieved_target_amount = fields.Monetary("Achieved Amount", compute="_compute_total")
    achieved_target_per = fields.Float("Achieved(%)", compute="_compute_total")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=False,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency', required=True, readonly=False,
        default=lambda self: self.env.company.currency_id)
    target_line_ids = fields.One2many('kg.target.lines', 'target_id', string="Target Lines")
    lead_target = fields.Integer('Lead Target', default=1)
    lead_target_freq = fields.Selection([('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')], string="Lead Frequency", default='daily', readonly=True)
    prop_target = fields.Integer('Proposal Target', default=1)
    prop_target_freq = fields.Selection(
        [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
        string="Lead Frequency", default='weekly', readonly=True)

    def get_year(self):
        year = fields.Datetime.now().strftime("%Y")
        return year

    def get_years(self):
        year_list = []
        for i in range(2021, 2050):
            year_list.append((str(i), str(i)))
        return year_list

    year = fields.Selection(get_years, string="Year", default=get_year, required=True)
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    monthly_target_lines = fields.One2many('monthly.target.lines', 'sales_target_id', string="Monthly Target Lines")

    _sql_constraints = [('salesperson_unique_mapping', 'unique(user_id, company_id)',
                         'Salesperson Target must be unique! \n You cannot set multiple sales target for same salesperson')]

    @api.depends('target_line_ids')
    @api.onchange('target_line_ids.target_per')
    def _compute_total(self):
        for rec in self:
            revenue_target_amt = 0
            for line in rec.target_line_ids:
                revenue_target_amt += line.revenue_head_id.tot_tar * line.target_per
            rec.annual_target_amount = revenue_target_amt
            rec.tot_per = (revenue_target_amt / sum(self.env['kg.revenue.head'].search([]).mapped('tot_tar'))) if sum(
                self.env['kg.revenue.head'].search([]).mapped('tot_tar')) else 0
            rec.monthly_target_lines = False
            month_lines = []
            split_lines = []
            for month in range(1, 13):
                tot_month_target = 0
                for line in rec.target_line_ids:
                    revenue_target = sum(line.revenue_head_id.mapped('month_target_lines').filtered(
                        lambda x: x.month == str(month) and x.year == rec.year).mapped('target')) * line.target_per
                    tot_month_target += revenue_target
                    if revenue_target:
                        split_lines.append({
                            'revenue_head_id': line.revenue_head_id.id,
                            'target': revenue_target,
                            'month': str(month),
                            'year': rec.year,
                        })
                month_lines.append((0, 0, {
                    'month': str(month),
                    'year': rec.year,
                    'target': tot_month_target,
                }))
            rec.monthly_target_lines = month_lines

            won_stage_id = self.env['crm.stage'].search([('is_won', '=', True)], limit=1).id
            all_leads = self.env['crm.lead'].search([('user_id', '=', rec.user_id.id), ('type', '=', 'opportunity')])
            won_leads = all_leads.filtered(lambda x: x.stage_id.id == won_stage_id and x.date_closed and rec.start_date <= x.date_closed.date() <= rec.end_date)
            achieved_amount = sum(won_leads.mapped('expected_revenue'))
            rec.achieved_target_amount = achieved_amount
            rec.achieved_target_per = (achieved_amount/revenue_target_amt) if revenue_target_amt else 0

    @api.onchange('name', 'year')
    def onchange_year(self):
        for rec in self:
            rec.start_date = rec.end_date = False
            month_date = date(int(rec.year), 1, 1)
            rec.start_date = month_date.replace(day=1)
            rec.end_date = month_date.replace(month=12, day=31)
            rev_lines = []
            for rev in self.env['kg.revenue.head'].search([('year', '=', rec.year)]):
                rev_lines.append((0, 0, {
                    'revenue_head_id': rev.id,
                }))
            rec.target_line_ids = rev_lines


class KgTargetLines(models.Model):
    _name = "kg.target.lines"

    target_id = fields.Many2one('kg.sales.target', string="Sales Target")
    revenue_head_id = fields.Many2one('kg.revenue.head', string="Revenue Head")
    target_per = fields.Float(string="Target(%)")
    unallocated_per = fields.Float(related="revenue_head_id.unallocated_per", string="Unallocated(%)")
    target_amount = fields.Monetary(string="Target", compute="_compute_target_amount")
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency', required=True, readonly=False,
        default=lambda self: self.env.company.currency_id)

    @api.onchange('revenue_head_id', 'target_per')
    def _compute_target_amount(self):
        for rec in self:
            rec.target_amount = rec.revenue_head_id.tot_tar * rec.target_per

    @api.onchange("month", "year")
    def onchange_month(self):
        self.start_date = self.end_date = False
        if self.month and self.year:
            month_date = date(int(self.year), int(self.month), 1)
            self.start_date = month_date.replace(day=1)
            self.end_date = month_date.replace(
                day=calendar.monthrange(month_date.year, month_date.month)[1]
            )
        elif self.year:
            month_date = date(int(self.year), 1, 1)
            self.start_date = month_date.replace(day=1)
            self.end_date = month_date.replace(month=12, day=31)


class MonthlyTargetLines(models.Model):
    _name = "monthly.target.lines"

    sales_target_id = fields.Many2one('kg.sales.target', string="Sales Target")
    revenue_split_ids = fields.Many2many('kg.revenue.split', string="Revenue Split")

    def get_year(self):
        year = fields.Datetime.now().strftime("%Y")
        return year

    def get_years(self):
        year_list = []
        for i in range(2021, 2050):
            year_list.append((str(i), str(i)))
        return year_list

    month = fields.Selection(
        [
            ("1", "January"),
            ("2", "February"),
            ("3", "March"),
            ("4", "April"),
            ("5", "May"),
            ("6", "June"),
            ("7", "July"),
            ("8", "August"),
            ("9", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Month", readonly=True
    )

    year = fields.Selection(get_years, string="Year", default=get_year, readonly=True)
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    target = fields.Monetary("Target")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company.currency_id)

    @api.onchange("month", "year")
    def onchange_month(self):
        self.start_date = self.end_date = False
        if self.month and self.year:
            month_date = date(int(self.year), int(self.month), 1)
            self.start_date = month_date.replace(day=1)
            self.end_date = month_date.replace(
                day=calendar.monthrange(month_date.year, month_date.month)[1]
            )
        elif self.year:
            month_date = date(int(self.year), 1, 1)
            self.start_date = month_date.replace(day=1)
            self.end_date = month_date.replace(month=12, day=31)

    def view_splits(self):
        target_lines = self.sales_target_id.mapped('target_line_ids')
        split_lines = []
        for line in target_lines:
            revenue_target = sum(line.revenue_head_id.mapped('month_target_lines').filtered(
                lambda x: x.month == str(self.month) and x.year == self.year).mapped('target')) * line.target_per
            if revenue_target:
                split_lines.append({
                    'revenue_head_id': line.revenue_head_id.id,
                    'target': revenue_target,
                    'month': str(self.month),
                    'year': self.year,
                    'target_per': line.target_per,
                })
        split_ids = self.env['kg.revenue.split'].create(split_lines)
        return {
                'type': 'ir.actions.act_window',
                'name': 'Monthly Targets',
                'res_model': 'kg.revenue.split',
                'view_mode': 'tree',
                'domain': [('id', 'in', split_ids.ids)],
                'target': 'new',
                'context': {'create': False},
            }