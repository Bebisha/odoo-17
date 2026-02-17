# -*- coding: utf-8 -*-
import calendar
from datetime import date
from odoo import api, fields, models


class KgRevenueHead(models.Model):
    _name = "kg.revenue.head"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Kg Revenue Head"
    _order = 'name desc'
    _rec_name = 'display_name'

    name = fields.Char(string='Name', required=True)
    display_name = fields.Char(string='Name', compute="_compute_display_name")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency', required=True, readonly=True,
        default=lambda self: self.env.company.currency_id)
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
    unallocated_per = fields.Float("Unallocated", compute="_compute_value")
    tot_tar = fields.Monetary("Annual Target", compute="_compute_value")
    month_target_lines = fields.One2many('revenue.head.lines', 'revenue_head_id', string="Revenue Head Lines")


    @api.onchange('name', 'year')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = " (" + str(rec.year) + ")"
            if rec.name:
                rec.display_name = rec.name + " (" + str(rec.year) + ")"

    @api.onchange("name","year")
    def onchange_year(self):
        for rec in self:
            rec.start_date = rec.end_date = False
            rec.month_target_lines = [(5, 0, 0)]  # Clear existing lines

            if rec.year and rec.year.isdigit():
                year_int = int(rec.year)
                rec.start_date = date(year_int, 1, 1)
                rec.end_date = date(year_int, 12, 31)

                month_lines = []
                for month in range(1, 13):
                    month_lines.append((0, 0, {
                        'month': str(month),
                        'year': rec.year,
                    }))

                rec.month_target_lines = month_lines

    @api.depends('month_target_lines')
    @api.onchange('month_target_lines.target')
    def _compute_value(self):
        for rec in self:
            rec.tot_tar = sum(rec.month_target_lines.mapped('target'))
            value = 1-sum(self.env['kg.sales.target'].search([]).mapped('target_line_ids').filtered(lambda x: x.revenue_head_id == rec).mapped('target_per'))
            value = 0 if abs(value) < 1e-10 else round(value, 2)
            rec.unallocated_per = value


class RevenueHeadLines(models.Model):
    _name = "revenue.head.lines"

    revenue_head_id = fields.Many2one('kg.revenue.head', string="Revenue Head")

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


class KgRevenueSplit(models.Model):
    _name = "kg.revenue.split"

    month_target_id = fields.Many2one('kg.revenue.split', string="Month target")
    revenue_head_id = fields.Many2one('kg.revenue.head', string="Revenue Head")
    target = fields.Float(string="Target")
    target_per = fields.Float(string="Target(%)")
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
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company.currency_id)