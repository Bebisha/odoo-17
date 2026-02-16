from datetime import date

from odoo import api, fields, models, _


class UnpaidInvoiceWizard(models.TransientModel):
    """Unpaid Invoice wizard."""

    _name = 'unpaid.invoice.report.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date(required=True, default=fields.Date.to_string(date.today()), string='As on')
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')

    def _export(self, report_type):
        return self._print_report(report_type)

    def button_unpaid_invoice_report(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def _print_report(self, data):
        res = {}
        data = {
            'model': 'unpaid.invoice.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_accounting.action_unpaid_invoice_report').with_context(
            landscape=False).report_action(self, data=data)
