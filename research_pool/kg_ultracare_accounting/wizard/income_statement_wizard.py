from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _


class IncomeStatementWizard(models.TransientModel):
    """Income Statement wizard."""

    _name = 'income.statement.report.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date(required=True,default=str(date.today()),string='As on')
    last_year = fields.Date('Last Year')
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')

    @api.onchange('date_from')
    def _onchange_last_year(self):
        for rec in self:
            if rec.date_from:
                rec.last_year = rec.date_from - relativedelta(years=1)

    def _export(self, report_type):
        return self._print_report(report_type)

    def button_income_statement_report(self):
            self.ensure_one()
            report_type = "qweb-pdf"
            return self._export(report_type)


    def _print_report(self, data):
        res = {}
        data = {
            'model': 'income.statement.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_accounting.kg_action_income_statement_report').with_context(
            landscape=False).report_action(self, data=data)
