# -*- coding: utf-8 -*-

import base64
from io import BytesIO

import xlwt

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BudgetUsageEntry(models.Model):
    _name = 'budget.usage.entry'
    _description = 'budget.usage.entry'

    name = fields.Char(string='Reference', default=lambda self: _('New'), readonly=True)
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    budget_days_ids = fields.One2many('budget.days', 'budget_usage_entry_id', string='Days')
    usage_per_day_ids = fields.One2many('usage.per.day', 'budget_usage_entry_id', string='Usage Per Day')
    total_usage_ids = fields.One2many('total.usage', 'budget_usage_entry_id', string='Total Usage')
    energy_cost_month_ids = fields.One2many('energy.cost.month', 'budget_usage_entry_id',
                                            string='Energy Cost For Month')

    @api.model
    def create(self, vals):
        """ Budget Usage Entry Sequence Number Generation """
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'budget.usage.entry.sequence') or _('New')
        return super(BudgetUsageEntry, self).create(vals)

    def get_data(self):
        """ Function to get data for the report """
        for budget in self:
            budget_list = []
            if budget:
                for usage in budget.budget_days_ids:
                    budget_data = {
                        'actual': usage.actual,
                        'budget': usage.budget,
                        'variance': usage.variance,
                        'activity': usage.activity_id.name,
                    }
                    budget_list.append(budget_data)
            return budget_list

    def print_report(self):
        """ Acton to print budget usage report """
        budget_list = self.get_data()
        if not budget_list:
            raise ValidationError("There is no data in the selected time period!")
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Budget Usage Report')

        from_date = fields.Date.to_date(self.date_from).strftime('%d %B %Y') if self.date_from else ''
        to_date = fields.Date.to_date(self.date_to).strftime('%d %B %Y') if self.date_to else ''

        bold_font_large = xlwt.Font()
        bold_font_large.bold = True
        bold_font_large.height = 350

        bold_style_large = xlwt.XFStyle()
        bold_style_large.font = bold_font_large
        alignment_large = xlwt.Alignment()
        alignment_large.horz = xlwt.Alignment.HORZ_CENTER
        bold_style_large.alignment = alignment_large

        bold_font_small = xlwt.Font()
        bold_font_small.bold = True
        bold_font_small.height = 220

        bold_style_small = xlwt.XFStyle()
        bold_style_small.font = bold_font_small
        alignment_small = xlwt.Alignment()
        alignment_small.horz = xlwt.Alignment.HORZ_CENTER
        bold_style_small.alignment = alignment_small

        right_align_style = xlwt.XFStyle()
        right_alignment = xlwt.Alignment()
        right_alignment.horz = xlwt.Alignment.HORZ_RIGHT
        right_align_style.alignment = right_alignment

        row_height = 30
        worksheet.row(6).set_style(xlwt.easyxf(f'font: height {row_height * 20};'))

        worksheet.write_merge(0, 1, 4, 8, 'Budget Usage Report', bold_style_large)
        worksheet.write_merge(3, 4, 4, 9, self.vessel_id.name, bold_style_large)

        worksheet.write_merge(8, 8, 4, 5, from_date, bold_style_small)
        worksheet.write_merge(8, 8, 6, 7, from_date, bold_style_small)

        worksheet.write_merge(9, 9, 1, 3, 'Days', bold_style_small)
        worksheet.write_merge(9, 9, 4, 5, 'Actual', bold_style_small)
        worksheet.write_merge(9, 9, 6, 7, 'Budget', bold_style_small)
        worksheet.write_merge(9, 9, 8, 9, 'Variance', bold_style_small)

        for row, budget in enumerate(budget_list, start=10):
            worksheet.write_merge(row, row, 1, 3, budget['activity'])
            worksheet.write_merge(row, row, 4, 5, budget['actual'])
            worksheet.write_merge(row, row, 6, 7, budget['budget'])
            worksheet.write_merge(row, row, 8, 9, round(budget['variance'], 2))


        # fuel_total_list = self.get_total_data()
        #
        # total_head_row = row + 3
        # worksheet.write_merge(total_head_row, total_head_row, 0, 3, 'Activity', bold_style_small)
        # worksheet.write_merge(total_head_row, total_head_row, 4, 5, 'MGO', bold_style_small)
        # worksheet.write_merge(total_head_row, total_head_row, 6, 7, 'HFO', bold_style_small)
        # worksheet.write_merge(total_head_row, total_head_row, 8, 9, 'Days', bold_style_small)
        #
        # for total_row, data in enumerate(fuel_total_list, start=total_head_row + 1):
        #     worksheet.write_merge(total_row, total_row, 0, 3, data['activity'])
        #     worksheet.write_merge(total_row, total_row, 4, 5, data['total_tons_mgo'])
        #     worksheet.write_merge(total_row, total_row, 6, 7, data['total_tons_hfo'])
        #     worksheet.write_merge(total_row, total_row, 8, 9, data['days'])
        #
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        attachment = self.env['ir.attachment'].create({
            'name': 'Budget_Usage_Report.xls',
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

class BudgetDays(models.Model):
    _name = 'budget.days'
    _description = 'budget.days'

    actual = fields.Float(string='Actual')
    budget = fields.Float(string='Budget')
    variance = fields.Float(string='Variance(%)', compute='_compute_variance')
    activity_id = fields.Many2one('budget.activity', string='Activity')
    budget_usage_entry_id = fields.Many2one('budget.usage.entry', string='Budget Usage Entry')

    @api.depends('actual', 'budget')
    def _compute_variance(self):
        for rec in self:
            if rec.actual and rec.budget:
                variance = ((rec.actual / rec.budget) - 1) * 100
                rec.write({
                    'variance': variance,
                })
            else:
                rec.variance = 0.0


class UsagePerDay(models.Model):
    _name = 'usage.per.day'
    _description = 'usage.per.day'

    actual = fields.Float(string='Actual')
    budget = fields.Float(string='Budget')
    variance = fields.Float(string='Variance(%)', compute='_compute_variance')
    activity_id = fields.Many2one('budget.activity', string='Activity')
    budget_usage_entry_id = fields.Many2one('budget.usage.entry', string='Budget Usage Entry')

    @api.depends('actual', 'budget')
    def _compute_variance(self):
        for rec in self:
            if rec.actual and rec.budget:
                variance = ((rec.actual / rec.budget) - 1) * 100
                rec.write({
                    'variance': variance,
                })
            else:
                rec.variance = 0.0


class TotalUsage(models.Model):
    _name = 'total.usage'
    _description = 'total.usage'

    actual = fields.Float(string='Actual')
    budget = fields.Float(string='Budget')
    variance = fields.Float(string='Variance(%)', compute='_compute_variance')
    activity_id = fields.Many2one('budget.activity', string='Activity')
    budget_usage_entry_id = fields.Many2one('budget.usage.entry', string='Budget Usage Entry')

    @api.depends('actual', 'budget')
    def _compute_variance(self):
        for rec in self:
            if rec.actual and rec.budget:
                variance = ((rec.actual / rec.budget) - 1) * 100
                rec.write({
                    'variance': variance,
                })
            else:
                rec.variance = 0.0


class EnergyCostForMonth(models.Model):
    _name = 'energy.cost.month'
    _description = 'energy.cost.month'

    actual = fields.Float(string='Actual')
    budget = fields.Float(string='Budget')
    variance = fields.Float(string='Variance(%)', compute='_compute_variance')
    activity_id = fields.Many2one('budget.activity', string='Activity')
    budget_usage_entry_id = fields.Many2one('budget.usage.entry', string='Budget Usage Entry')

    @api.depends('actual', 'budget')
    def _compute_variance(self):
        for rec in self:
            if rec.actual and rec.budget:
                variance = ((rec.actual / rec.budget) - 1) * 100
                rec.write({
                    'variance': variance,
                })
            else:
                rec.variance = 0.0
