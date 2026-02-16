from datetime import date

from odoo import api, fields, models, _


class OpeningBalanceWizard(models.TransientModel):
    """Opening Balance wizard."""

    _name = 'opening.balance.report.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date(required=True,default=str(date.today()),string='As on')
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')


    def _export(self, report_type):
        return self._print_report(report_type)



    def button_opening_balance_report(self):
            self.ensure_one()
            report_type = "qweb-pdf"
            return self._export(report_type)


    def _print_report(self, data):
        res = {}
        data = {
            'model': 'opening.balance.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_accounting.kg_action_opening_balance_report').with_context(
            landscape=False).report_action(self, data=data)
