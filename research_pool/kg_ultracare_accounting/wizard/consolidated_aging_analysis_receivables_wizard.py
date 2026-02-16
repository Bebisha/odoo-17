# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################
import time

# from pkg_resources import _

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
# ========For Excel========
from io import BytesIO
import xlwt
from xlwt import easyxf
import base64


# =====================

class ConsolidatedAgingAnalysisWizard(models.TransientModel):
    _name = 'consolidated.aging.analysis.wizard'
    _description = 'Consolidated Ageing Analysis'

    period_length = fields.Integer('Period Length (Days)', default=30, required="1")
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True)
    date_from = fields.Date(default=lambda *a: time.strftime('%Y-%m-%d'))
    period_length_months = fields.Integer(string='Period Length (months)', required=True, default=1)
    period_length_type = fields.Selection([
        ('months', 'Months'),
        ('days', 'Days'),
    ], default='days', required=True)
    heading = fields.Char(compute='_get_heading')
    partner_type = fields.Char(compute='_get_type')
    un_even = fields.Boolean(default=False)
    period_length_uneven = fields.Integer(string='Period Length (days)', required=True)
    period_ids = fields.One2many('account.aged.trial.balance.line', 'line_id')
    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                         ('supplier', 'Payable Accounts'),
                                         ('customer_supplier', 'Receivable and Payable Accounts')
                                         ], string="Partner's", required=True, default='customer')
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')


    @api.onchange('period_length_type')
    def change_period_length_type(self):
        if self.period_length_type == 'months':
            self.un_even = False
            self.period_length_uneven = 0

    @api.onchange('period_length_uneven')
    def period_even(self):
        if self.period_length_uneven:
            self.period_ids = False
            lines = []
            j = 1
            for i in range(self.period_length_uneven):
                line_data = {
                    "period": 0,
                    'si_no': j
                }
                lines.append((0, 0, line_data))
                j += 1
            self.period_ids = lines

    def _get_heading(self):
        for each in self:
            if each.period_length_type == 'days':
                each.heading = 'CONSOLIDATED AGING ANALYSIS (DAY WISE)'
            if each.period_length_type == 'months':
                each.heading = 'CONSOLIDATED AGING ANALYSIS (MONTH WISE)'

    def _get_type(self):
        for each in self:
            if each.result_selection == 'customer':
                each.partner_type = 'Receivable Accounts'
            elif each.result_selection == 'supplier':
                each.partner_type = 'Payable Accounts'
            else:
                each.partner_type = 'Receivable and Payable Accounts'

    def _export(self, report_type):
        return self._print_report(report_type)

    def button_payable(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def _get_report_data(self, data):
        res = {}
        per_len = self.read()
        data['form']['period_length'] = per_len[0].get('period_length')
        data['form']['period_length_months'] = per_len[0].get('period_length_months')
        data['form']['period_length_type'] = per_len[0].get('period_length_type')
        data['form']['un_even'] = per_len[0].get('un_even')
        data['form']['period_length_uneven'] = per_len[0].get('period_length_uneven')
        data['form']['heading'] = per_len[0].get('heading')
        data['form']['partner_type'] = per_len[0].get('partner_type')
        period_length = data['form']['period_length']
        period_length_months = data['form']['period_length_months']
        period_length_type = data['form']['period_length_type']

        if period_length_type == 'days':
            if period_length <= 0:
                raise UserError(_('You must set a period length greater than 0.'))
            if self.un_even:
                if self.period_length_uneven <= 0:
                    raise UserError(_('You must set a period length greater than 0.'))
                if any(line.period == 0 for line in self.period_ids):
                    raise UserError(_('You must set  period  greater than 0.'))
        if period_length_type == 'months':
            if period_length_months <= 0:
                raise UserError(_('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise UserError(_('You must set a start date.'))

        start = data['form']['date_from']
        stop = start.replace(day=1)
        count = period_length_months
        range_count = 6
        if period_length_type == 'months':
            range_count = period_length_months
            data['form'].update(self.read(['period_length_type'])[0])
            for i in range(period_length_months)[period_length_months::-1]:
                # stop = start - relativedelta(months=period_length_months - count)
                if i == 0:
                    period_name = '>=' + str(stop.strftime("%b")) + '-' + str(stop.year)
                else:
                    period_name = str(stop.strftime("%b")) + '-' + str(stop.year)
                period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
                # if i == 0:
                # period_name = '+' + str(4 * period_length)
                res[str(i)] = {
                    'name': period_name,  # Heading name that goes to report
                    'stop': period_stop,
                    'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
                    'range': range_count,
                }
                stop = start - relativedelta(months=1)

                start = stop
                count = count - 1

        if period_length_type == 'days':
            if self.un_even:
                first = self.period_ids[0]
                period_list = []
                inside = 0
                for line in self.period_ids:
                    if inside == 0:
                        dict = {'name': '0-' + str(line.period), 'period': line.period}
                        inside = 1
                        period_list.append(dict)
                        first = line.period
                    else:
                        last = first + line.period
                        dict = {'name': str(first) + '-' + str(last), 'period': line.period}
                        period_list.append(dict)
                        first = last
                i = self.period_length_uneven
                for data1 in period_list:
                    stop = start - relativedelta(days=data1['period'])
                    res[str(i)] = {
                        'name': data1['name'],
                        'stop': start.strftime('%Y-%m-%d'),
                        'start': stop.strftime('%Y-%m-%d') or False,
                        'range': self.period_length_uneven + 1,
                    }
                    i -= 1
                    start = stop - relativedelta(days=1)
                res[str(i)] = {
                    'name': "+" + str(last),
                    'stop': start.strftime('%Y-%m-%d'),
                    'start': False,
                    'range': self.period_length_uneven + 1,
                }
                data.update({'periods': res})
            else:
                for i in range(6)[::-1]:
                    stop = start - relativedelta(days=period_length - 1)
                    res[str(i)] = {
                        'name': (i != 0 and (
                                str((6 - (i + 1)) * period_length) + '-' + str(
                            (6 - i) * period_length)) or (
                                         '+' + str(5 * period_length))),
                        'stop': start.strftime('%Y-%m-%d'),
                        'start': (i != 0 and stop.strftime('%Y-%m-%d') or False),
                        'range': range_count,
                    }
                    start = stop - relativedelta(days=1)
        data['form'].update(res)
        return data

    def _print_report(self, data):
        res = {}

        data = {
            'model': 'consolidated.aging.analysis.wizard',
            'form': self.read()[0]
        }
        data = self._get_report_data(data)
        return self.env.ref('kg_ultracare_accounting.action_report_consolidated_aging_receivables'). \
            with_context(landscape=True).report_action(self, data=data)


class AccountAgedTrialBalanceLine(models.TransientModel):
    _name = 'account.aged.trial.balance.line'

    line_id = fields.Many2one('account.aged.trial.balance')
    si_no = fields.Integer()
    period = fields.Integer()


