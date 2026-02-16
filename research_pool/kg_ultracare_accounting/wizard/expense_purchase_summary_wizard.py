from datetime import date

from odoo import api, fields, models, _
from odoo.tools.safe_eval import datetime
import time


class ExpensePurchaseSummaryWizard(models.TransientModel):
    """Expense Purchase Summary wizard."""

    _name = 'expense.purchase.summary.report.wizard'
    _description = 'Report Wizard'

    @api.model
    def year_selection(self):
        year = 2020  # replace 2000 with your a start year
        year_list = []
        while year != 3051:  # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    year = fields.Selection(year_selection, string="Year", default=str(datetime.datetime.now().year))
    current_year = fields.Char('Current Year', default=datetime.datetime.now().year)
    date_from = fields.Date()
    date_to = fields.Date()
    currency_id = fields.Many2one('res.currency', string="Currency",default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id, string='Company')

    @api.onchange('year')
    def get_start_end_year(self):
        if self.year == self.current_year:
            start = '01-01-' + str(self.year)
            end = date.today()
            self.date_from = datetime.datetime.strptime(start, '%d-%m-%Y')
            self.date_to = end
        if self.year != self.current_year:
            start = '01-01-' + str(self.year)
            end = '31-12-' + str(self.year)
            self.date_from = datetime.datetime.strptime(start, '%d-%m-%Y')
            self.date_to = datetime.datetime.strptime(end, '%d-%m-%Y')


    def _export(self, report_type):
        return self._print_report(report_type)

    def button_expense_pur_sum_report(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def _print_report(self, data):
        res = {}
        data = {
            'model': 'expense.purchase.summary.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_accounting.action_expense_pur_sum_report').with_context(
            landscape=False).report_action(self, data=data)