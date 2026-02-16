import time
from odoo import api, models, _
from odoo.exceptions import UserError, ValidationError


class AccountReceivablesLedgerReport(models.AbstractModel):
    _name = 'report.kg_ultracare_accounting.account_receivable_template_id'
    _description = 'Account Receivables Ledger Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model') or not self.env.context.get('active_id'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        model = self.env.context.get('active_model')
        company_id = data['form'].get('company_id')
        date_from = data['form'].get('date_from', time.strftime('%Y-%m-%d'))
        browsed_currency_id = data['form'].get('currency_id')
        currency_id = self.env['res.currency'].browse(browsed_currency_id[0])
        browsed_company = self.env['res.company'].browse(company_id[0])

        data = []
        total_invoice_amount = 0
        total_paid_amount = 0
        total_balance = 0
        total_pdc_amount = 0

        customer_id = self.env['res.partner'].search([])
        for cus in customer_id:
            account_list = {
                'type': 'customer',
                'customer_name': str(cus.name).upper(),
                'customer_code': str(cus.customer_code).upper()
            }
            account_move_id = self.env['account.move.line'].search(
                [('date', '>=', date_from), ('move_id.state', '=', 'posted'), ('partner_id', '=', cus.id)],
                order='date asc')
            if len(account_move_id) > 0:
                data.append(account_list)
            if account_move_id:
                for vals in account_move_id:
                    date = vals.date
                    journal_type = vals.journal_id.name
                    # doc_no = vals.move_name
                    ref = vals.ref
                    ref_date = vals.invoice_date
                    invoice_amount = vals.move_id.amount_total
                    paid_amount = vals.move_id.amount_paid
                    balance = vals.balance
                    pdc_amount = vals.move_id.total_pdc_payment

                    account_list = {
                        'type': 'data',
                        'date': date,
                        'journal_type': journal_type,
                        # 'doc_no': doc_no,
                        'ref': ref,
                        'ref_date': ref_date,
                        'invoice_amount': invoice_amount,
                        'paid_amount': paid_amount,
                        'balance': balance,
                        'pdc_amount': pdc_amount,
                    }
                    data.append(account_list)

                    total_invoice_amount += invoice_amount
                    total_paid_amount += paid_amount
                    total_balance += balance
                    total_pdc_amount += pdc_amount

            account_list = {
                'type': 'amount',
                'total_invoice_amount': total_invoice_amount,
                'total_paid_amount': total_paid_amount,
                'total_balance': total_balance,
                'total_pdc_amount': total_pdc_amount,
            }
            if total_invoice_amount or total_paid_amount or total_balance or total_pdc_amount != 0:
                data.append(account_list)

            total_invoice_amount = 0
            total_paid_amount = 0
            total_balance = 0
            total_pdc_amount = 0

        return {
            'doc_ids': self.ids,
            'datas': data,
            'doc_model': model,
            'currency_id': currency_id,
            'company_id': browsed_company.name,
            'company_zip': browsed_company.zip,
            'company_state': browsed_company.state_id.name,
            'company_country': browsed_company.country_id.name,
            'date_from': date_from
        }
