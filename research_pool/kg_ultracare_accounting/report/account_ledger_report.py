import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import image_data_uri


class AccountLedgerReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.account_ledger_template_id'
    _description = 'Account Ledger Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        date_end = data['form'].get('date_to', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        account_id = self.env['account.account'].search([])
        for acc in account_id:
            account_list = {
                'type': 'account',
                'account_code': str(acc.code).upper(),
                'account_name': str(acc.name).upper()
            }
            account_move_line_id = self.env['account.move.line'].search(
                [('date', '>=', date_from), ('move_id.state', '=', 'posted'), ('account_id', '=', acc.id)])
            if len(account_move_line_id) > 0:
                data.append(account_list)
            if account_move_line_id:
                for vals in account_move_line_id:
                    date = vals.date
                    doc_type = str(vals.journal_id.type).upper()
                    doc_no = vals.move_name
                    # ref_no =
                    currency = vals.currency_id.name
                    reference = vals.ref
                    debit = vals.debit
                    credit = vals.credit
                    balance = vals.balance


                    account_list = {
                        'type': 'data',
                        'date': date,
                        'doc_type': doc_type,
                        'doc_no': doc_no,
                        # 'ref_no': ref_no,
                        'reference': reference,
                        'currency': currency,
                        'credit': credit,
                        'debit': debit,
                        'balance': balance,
                    }
                    data.append(account_list)

        # if not data:
        #     raise ValidationError(_('No data in this date range'))

        return {
            'doc_ids': self.ids,
            'datas': data,
            'from_date': date_from,
            'to_date': date_end,
            'doc_model': model,
            'currency_id': currency_id.name,
            'company_id': browsed_company.name,
            'company_details': browsed_company.company_details,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'company_bank_name': browsed_company.bank.name,
        }
