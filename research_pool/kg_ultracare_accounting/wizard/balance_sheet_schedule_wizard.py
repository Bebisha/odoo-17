from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BalanceSheetScheduleWizard(models.TransientModel):
    """Balance Sheet Schedule wizard."""

    _name = 'balance.sheet.schedule.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')


    def _export(self, report_type):
        return self._print_report(report_type)


    def button_balance_sheet_schedule_report(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))
        else:
            self.ensure_one()
            report_type = "qweb-pdf"
            return self._export(report_type)


    def _print_report(self, data):
        res = {}
        data = {
            'model': 'balance.sheet.schedule.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_accounting.action_balance_sheet_schedule_report').with_context(
            landscape=False).report_action(self, data=data)
