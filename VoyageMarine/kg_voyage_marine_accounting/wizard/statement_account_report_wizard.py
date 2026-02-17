from datetime import date

from odoo.exceptions import ValidationError
from odoo.tools import image_data_uri
from odoo import models, fields, api


class StatementAccountWizard(models.TransientModel):
    _name = "statement.account.report.wizard"
    _description = "Statement of Account Wizard"

    def get_outstanding_partner_ids(self):
        invoice_ids = self.env['account.move'].search(
            [('invoice_date_due', '<=', date.today()), ('move_type', 'in', ['out_invoice', 'in_refund']),
             ('state', '=', 'posted'), ('payment_state', 'in', ['partial', 'not_paid'])])

        outstanding_partner_ids = self.env['res.partner'].search(
            [('id', 'in', invoice_ids.mapped('partner_id').ids), ('state', '=', 'approval')])

        return outstanding_partner_ids.ids

    name = fields.Char(string="Reference")

    partner_id = fields.Many2one("res.partner", string="Partner")
    account_type = fields.Selection([("asset_receivable", "Receivable"), ("liability_payable", "Payable")],
                                    default="asset_receivable")

    outstanding_partner_ids = fields.Many2many("res.partner", string="Outstanding Partners",
                                               default=get_outstanding_partner_ids)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.company,
                                 string='Company')
    date_to = fields.Date(required=True, default=date.today(), string='As on')

    @api.onchange('account_type', 'date_to')
    def outstanding_partners(self):
        for rec in self:
            if rec.account_type and rec.date_to:
                move_types = ['out_invoice', 'in_refund'] if rec.account_type == 'asset_receivable' else ['in_invoice',
                                                                                                          'out_refund']

                invoice_ids = self.env['account.move'].search([
                    ('invoice_date_due', '<=', rec.date_to),
                    ('move_type', 'in', move_types),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['partial', 'not_paid']),
                ], order='invoice_date asc')

                partner_ids = invoice_ids.mapped('partner_id').filtered(lambda p: p.state == 'approval')
                rec.outstanding_partner_ids = [(6, 0, partner_ids.ids)]

    def print_soa_report(self):
        if self.partner_id:
            partners = self.partner_id
        elif self.outstanding_partner_ids:
            partners = self.outstanding_partner_ids
        else:
            partners = self.env['res.partner'].search([])

        if not partners:
            raise ValidationError("Please select at least one partner.")

        if self.account_type == 'asset_receivable':
            account_type = 'asset_receivable'
            pdc_payment_type = 'receive_money'
        else:
            account_type = 'liability_payable'
            pdc_payment_type = 'send_money'

        # -------------------------------
        # SQL: Customer Statement + Aging
        # -------------------------------
        sql = """
            SELECT
                aml.partner_id,
                rp.name AS partner_name,
                am.name AS move_name,
                am.ref AS move_ref,
                am.payment_reference AS payment_ref,
                am.invoice_date,
                aml.date AS entry_date,
                COALESCE(aml.date_maturity, aml.date) AS due_date,
            
                aml.amount_residual,
                aml.amount_residual_currency,
                aml.amount_currency,
                aml.currency_id,
                rc.symbol AS currency_symbol,
                rc.position AS cur_position,
                aml.balance AS original_balance,
                am.vessel_id,
            
                /* AT DATE (NOT YET DUE) */
                    CASE
                        WHEN aml.amount_residual > 0
                         AND (%(date_to)s - COALESCE(aml.date_maturity, aml.date)) < 0
                        THEN aml.amount_residual
                        ELSE 0
                    END AS age_at_date,
                    
                    /* 0–30 */
                    CASE
                        WHEN aml.amount_residual > 0
                         AND (%(date_to)s - COALESCE(aml.date_maturity, aml.date)) BETWEEN 0 AND 30
                        THEN aml.amount_residual
                        ELSE 0
                    END AS age_0_30,
                    
                    /* 31–60 */
                    CASE
                        WHEN aml.amount_residual > 0
                         AND (%(date_to)s - COALESCE(aml.date_maturity, aml.date)) BETWEEN 31 AND 60
                        THEN aml.amount_residual
                        ELSE 0
                    END AS age_31_60,
                    
                    /* 61–90 (STRICT) */
                    CASE
                        WHEN aml.amount_residual > 0
                         AND (%(date_to)s - COALESCE(aml.date_maturity, aml.date)) BETWEEN 61 AND 90
                        THEN aml.amount_residual
                        ELSE 0
                    END AS age_61_90,
                    
                    /* 91+ (ODOO STYLE) */
                    CASE
                        WHEN aml.amount_residual > 0
                         AND (%(date_to)s - COALESCE(aml.date_maturity, aml.date)) > 90
                        THEN aml.amount_residual
                    
                        WHEN aml.amount_residual < 0
                        THEN aml.amount_residual   -- credits always here
                    
                        ELSE 0
                    END AS age_91_above


            
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN res_partner rp ON rp.id = aml.partner_id
            JOIN res_currency rc ON rc.id = aml.currency_id
            JOIN account_account aa ON aa.id = aml.account_id
            
            WHERE
                aml.partner_id IN %(partner_ids)s
                AND aa.account_type = %(account_type)s
                AND am.state = 'posted'
                AND am.pdc_id IS NULL
                AND aml.amount_residual != 0
                AND aml.date <= %(date_to)s
            
            ORDER BY
                rp.name,
                due_date;
        """

        self.env.cr.execute(sql, {
            'partner_ids': tuple(partners.ids),
            'date_to': self.date_to,
            'account_type': account_type,
        })

        rows = self.env.cr.dictfetchall()

        # -------------------------------
        # Build Report Structure
        # -------------------------------
        vals = []
        aging_values = {
            'at_date': 0.0,
            '0-30': 0.0,
            '31-60': 0.0,
            '61-90': 0.0,
            '91-above': 0.0,
        }

        partner_map = {}

        for r in rows:
            pid = r['partner_id']

            if pid not in partner_map:
                partner = self.env['res.partner'].browse(pid)
                partner_map[pid] = {
                    'partner_name': partner.name,
                    'partner_zip': partner.zip,
                    'partner_phone': partner.phone,
                    'partner_state': partner.state_id.name,
                    'partner_country': partner.country_id.code,
                    'inv_vals': [],
                    'partner_aging_values': {
                        'at_date': 0.0,
                        '0-30': 0.0,
                        '31-60': 0.0,
                        '61-90': 0.0,
                        '91-above': 0.0,
                    },
                    'outstanding_amt': 0.0,
                    'unadjusted_credit': 0.0,
                    'gross_outstanding_amt': 0.0,
                    'pdc_unmatured_amt': 0.0,
                    'settled_amt': 0.0,
                    'is_last_page_of_partner': True,
                }

            pdata = partner_map[pid]

            currency = self.company_id.currency_id
            entry_currency = r['currency_symbol']
            cur_position = r['cur_position']
            amount_residual_currency = abs(r['amount_residual_currency'])
            amount_residual = abs(r['amount_residual'])

            # ORIGINAL AMOUNT = balance before partial payments
            amount_currency = abs(r['amount_currency'])
            original_amount = abs(r['original_balance'])

            received_amount = original_amount - amount_residual
            received_amount_signed = amount_currency - amount_residual_currency

            vessel_name = ''
            if r['vessel_id']:
                vessel_name = self.env['vessel.code'].browse(r['vessel_id']).name

            pdata['inv_vals'].append({
                'inv_date': r['invoice_date'] or r['entry_date'],
                'inv_name': r['move_name'],
                'inv_ref': r['move_ref'] or r['payment_ref'],
                'vessel_name': vessel_name,
                'inv_amount': f"{amount_currency:.2f} {entry_currency}" if cur_position == 'after' else f"{entry_currency} {amount_currency:.2f}",
                'received_amount': f"{received_amount_signed:.2f} {entry_currency}" if cur_position == 'after' else f"{entry_currency} {received_amount_signed:.2f}",
                'balance_amount': f"{amount_residual_currency:.2f} {entry_currency}" if cur_position == 'after' else f"{entry_currency} {amount_residual_currency:.2f}",
                'outstanding_amount_aed': f"{amount_residual:.2f} {currency.symbol}",
                # 'inv_amount': f"{original_amount:.2f} {currency.symbol}",
                # 'received_amount': f"{received_amount:.2f} {currency.symbol}",
                # 'balance_amount': f"{amount_residual:.2f} {currency.symbol}",
                # 'outstanding_amount_aed': f"{amount_residual:.2f} {currency.symbol}",
            })

            pdata['outstanding_amt'] += r['amount_residual']

            # Totals
            pdata['partner_aging_values']['at_date'] += r['age_at_date']
            pdata['partner_aging_values']['0-30'] += r['age_0_30']
            pdata['partner_aging_values']['31-60'] += r['age_31_60']
            pdata['partner_aging_values']['61-90'] += r['age_61_90']
            pdata['partner_aging_values']['91-above'] += r['age_91_above']

            aging_values['at_date'] += r['age_at_date']
            aging_values['0-30'] += r['age_0_30']
            aging_values['31-60'] += r['age_31_60']
            aging_values['61-90'] += r['age_61_90']
            aging_values['91-above'] += r['age_91_above']

        # -------------------------------
        # PDC (Unmatured)
        # -------------------------------
        pdc_sql = """
            SELECT partner_id, SUM(payment_amount) AS pdc_amt
            FROM pdc_wizard
            WHERE payment_type = %(payment_type)s
              AND state IN ('registered','deposited','done')
              AND cheque_date >= %(date_to)s
              AND partner_id IN %(partner_ids)s
            GROUP BY partner_id
        """

        self.env.cr.execute(pdc_sql, {
            'partner_ids': tuple(partners.ids),
            'date_to': self.date_to,
            'payment_type': pdc_payment_type,
        })

        pdc_data = self.env.cr.dictfetchall()

        if not rows and not pdc_data:
            raise ValidationError("There is no data available in this date range !!")

        for r in pdc_data:
            pid = r['partner_id']

            # If partner not already created via SOA rows, create it now
            if pid not in partner_map:
                partner = self.env['res.partner'].browse(pid)
                partner_map[pid] = {
                    'partner_name': partner.name,
                    'partner_zip': partner.zip,
                    'partner_phone': partner.phone,
                    'partner_state': partner.state_id.name,
                    'partner_country': partner.country_id.code,
                    'inv_vals': [],
                    'partner_aging_values': {
                        'at_date': 0.0,
                        '0-30': 0.0,
                        '31-60': 0.0,
                        '61-90': 0.0,
                        '91-above': 0.0,
                    },
                    'outstanding_amt': 0.0,
                    'unadjusted_credit': 0.0,
                    'gross_outstanding_amt': 0.0,
                    'pdc_unmatured_amt': 0.0,
                    'settled_amt': 0.0,
                    'is_last_page_of_partner': True,
                }

            partner_map[pid]['pdc_unmatured_amt'] = r['pdc_amt'] or 0.0

        for pdata in partner_map.values():
            pdata['gross_outstanding_amt'] = pdata['outstanding_amt']
            pdata['settled_amt'] = pdata['outstanding_amt'] - pdata['pdc_unmatured_amt']
            vals.append(pdata)

        # -------------------------------
        # Company Bank
        # -------------------------------
        company_bank = []
        for bank in self.company_id.bank_ids.filtered('is_default'):
            company_bank.append({
                'acc_name': bank.acc_holder_name,
                'currency_id': bank.currency_id.name,
                'bank_name': bank.bank_id.display_name,
                'acc_number': bank.acc_number,
                'iban_number': bank.bank_iban_number,
                'swift_code': bank.bank_id.bic,
            })

        data = {
            'company_logo': self.company_id.logo and image_data_uri(self.company_id.logo) or '',
            'company_name': self.company_id.name,
            'company_zip': self.company_id.zip,
            'company_phone': self.company_id.phone,
            'company_mobile': self.company_id.mobile,
            'company_email': self.company_id.email,
            'company_website': self.company_id.website,
            'company_vat': self.company_id.vat,
            'company_city': self.company_id.city,
            'company_state': self.company_id.state_id.name,
            'company_country': self.company_id.country_id.code,
            'date_to': self.date_to,
            'values': vals,
            'aging_values': aging_values,
            'company_bank': company_bank,
            'account_type': self.account_type,
        }

        return self.env.ref(
            'kg_voyage_marine_accounting.action_soa_report'
        ).report_action(self, data=data)

    # def print_soa_report(self):
    #     vals = []
    #     age_brackets = {
    #         '0-30': (0, 30),
    #         '31-60': (31, 60),
    #         '61-90': (61, 90),
    #         '91-above': (91, float('inf')),
    #     }
    #     aging_values = {key: 0.0 for key in age_brackets.keys()}
    #
    #     if self.partner_id:
    #         partners = self.partner_id
    #     else:
    #         partners = self.env['res.partner'].search([('id', 'in', self.outstanding_partner_ids.ids)])
    #
    #     for partner in partners:
    #         if partner:
    #             if self.account_type == 'asset_receivable':
    #                 invoice_ids = self.env['account.move'].search([
    #                     ('invoice_date_due', '<=', self.date_to),
    #                     ('move_type', 'in', ['out_invoice', 'out_refund']),
    #                     ('state', '=', 'posted'),
    #                     ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id', '=', partner.id)
    #                 ], order='invoice_date asc')
    #                 move_lines = self.env['account.move.line'].search([
    #                     ('account_type', '=', 'asset_receivable'),
    #                     ('partner_id', '=', partner.id), ('move_type', 'in', ['entry']),
    #                     ('move_id.state', '=', 'posted'), ('ref', 'ilike', 'Customer Balance'),
    #                     ('date', '<=', self.date_to)
    #                 ], order='date asc').filtered(lambda x: not x.move_id.payment_id)
    #
    #             else:
    #                 invoice_ids = self.env['account.move'].search([
    #                     ('invoice_date_due', '<=', self.date_to),
    #                     ('move_type', 'in', ['in_invoice', 'in_refund']),
    #                     ('state', '=', 'posted'),
    #                     ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id', '=', partner.id)
    #                 ], order='invoice_date asc')
    #
    #                 move_lines = self.env['account.move.line'].search([
    #                     ('account_type', '=', 'liability_payable'),
    #                     ('partner_id', '=', partner.id), ('move_type', 'in', ['entry']),
    #                     ('move_id.state', '=', 'posted'), ('ref', 'ilike', 'Supplier Balance'),
    #                     ('date', '<=', self.date_to)
    #                 ], order='date asc').filtered(lambda x: not x.move_id.payment_id)
    #
    #             if invoice_ids:
    #                 partner_aging_values = {key: 0.0 for key in age_brackets.keys()}
    #                 outstanding_amt = 0.00
    #                 unadjusted_credit = 0.00
    #                 gross_outstanding_amt = 0.00
    #                 pdc_unmatured_amt = 0.00
    #                 settled_amt = 0.00
    #                 outstanding_amount_aed_total = 0.00
    #                 partners = {
    #                     'partner_name': partner.name,
    #                     'partner_zip': partner.zip,
    #                     'partner_phone': partner.phone,
    #                     'partner_state': partner.state_id.name,
    #                     'partner_country': partner.country_id.code,
    #                     'inv_vals': [],
    #                     'partner_aging_values': partner_aging_values,
    #                     'outstanding_amt': outstanding_amt,
    #                     'unadjusted_credit': unadjusted_credit,
    #                     'gross_outstanding_amt': gross_outstanding_amt,
    #                     'pdc_unmatured_amt': pdc_unmatured_amt,
    #                     'settled_amt': settled_amt,
    #                 }
    #                 for inv in invoice_ids:
    #                     paid_amount = inv.amount_total - inv.amount_residual
    #                     currency = inv.currency_id
    #
    #                     outstanding_amt += inv.amount_residual_signed if inv.move_type in ['out_invoice',
    #                                                                                        'in_invoice'] else 0.00
    #
    #                     days_overdue = (self.date_to - inv.invoice_date_due).days if inv.invoice_date_due else 0
    #                     for bracket, (min_days, max_days) in age_brackets.items():
    #                         if min_days <= days_overdue <= max_days:
    #                             partner_aging_values[bracket] += inv.amount_residual_signed
    #                             break
    #
    #                     outstanding_amount_aed = inv.amount_residual_signed if inv.move_type in ['out_invoice',
    #                                                                                              'in_invoice'] else 0.00
    #
    #                     outstanding_amount_aed_total += outstanding_amount_aed
    #
    #                     if inv.move_type in ['out_invoice', 'in_invoice']:
    #                         lines = {
    #                             'inv_date': inv.invoice_date,
    #                             'inv_name': inv.name,
    #                             'inv_ref': inv.ref,
    #                             'vessel_name': inv.vessel_id.name,
    #                             'inv_amount': f"{inv.amount_total:.2f}{' '}{currency.symbol}" if inv.move_type == 'out_invoice' else f"{-inv.amount_total:.2f}{' '}{currency.symbol}",
    #                             'received_amount': f"{paid_amount:.2f}{' '}{currency.symbol}" if inv.move_type == 'out_invoice' else f"{-paid_amount:.2f}{' '}{currency.symbol}",
    #                             'balance_amount': f"{inv.amount_residual:.2f}{' '}{currency.symbol}" if inv.move_type == 'out_invoice' else f"{-inv.amount_residual:.2f}{' '}{currency.symbol}",
    #                             'outstanding_amount_aed': f"{abs(outstanding_amount_aed_total):.2f}{' '}{'AED'}",
    #                         }
    #                         partners['inv_vals'].append(lines)
    #                 if move_lines:
    #                     for inv_line in move_lines:
    #                         currency = inv_line.currency_id
    #
    #                         outstanding_amt += inv_line.balance
    #
    #                         days_overdue = (self.date_to - inv_line.date).days if inv_line.date else 0
    #                         for bracket, (min_days, max_days) in age_brackets.items():
    #                             if min_days <= days_overdue <= max_days:
    #                                 partner_aging_values[bracket] += inv_line.balance
    #                                 break
    #                         outstanding_amount_aed = inv_line.balance
    #
    #                         outstanding_amount_aed_total += outstanding_amount_aed
    #
    #                         entry_lines = {
    #                             'inv_date': inv_line.date,
    #                             'inv_name': inv_line.name,
    #                             'inv_ref': inv_line.move_id.ref,
    #                             'vessel_name': inv_line.move_id.vessel_id.name,
    #                             'inv_amount': f"{0.00:.2f}{' '}{currency.symbol}",
    #                             'received_amount': f"{inv_line.balance:.2f}{' '}{currency.symbol}",
    #                             'balance_amount': f"{inv_line.balance:.2f}{' '}{currency.symbol}",
    #                             'outstanding_amount_aed': f"{abs(outstanding_amount_aed_total):.2f}{' '}{'AED'}",
    #                         }
    #                         partners['inv_vals'].append(entry_lines)
    #
    #                 if self.account_type == 'asset_receivable':
    #                     pdc_ids = self.env['pdc.wizard'].search(
    #                         [('partner_id', '=', partner.id), ('payment_type', '=', 'receive_money'),
    #                          ('state', 'in', ['registered', 'deposited', 'done']), ('due_date', '>=', self.date_to)])
    #                     if pdc_ids:
    #                         pdc_unmatured_amt = sum(pdc_ids.mapped('payment_amount'))
    #
    #                     unadjusted_invoice_ids = self.env['account.move'].search([
    #                         ('invoice_date_due', '<=', self.date_to),
    #                         ('move_type', 'in', ['out_refund']),
    #                         ('state', '=', 'posted'),
    #                         ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id', '=', partner.id)
    #                     ])
    #
    #                     if unadjusted_invoice_ids:
    #                         unadjusted_credit = sum(unadjusted_invoice_ids.mapped('amount_residual_signed'))
    #
    #                 else:
    #                     pdc_ids = self.env['pdc.wizard'].search(
    #                         [('partner_id', '=', partner.id), ('payment_type', '=', 'send_money'),
    #                          ('state', 'in', ['registered', 'deposited', 'done']), ('due_date', '>=', self.date_to)])
    #                     if pdc_ids:
    #                         pdc_unmatured_amt = sum(pdc_ids.mapped('payment_amount'))
    #
    #                     unadjusted_invoice_ids = self.env['account.move'].search([
    #                         ('invoice_date_due', '<=', self.date_to),
    #                         ('move_type', 'in', ['in_refund']),
    #                         ('state', '=', 'posted'),
    #                         ('payment_state', 'in', ['not_paid', 'partial']), ('partner_id', '=', partner.id)
    #                     ])
    #                     if unadjusted_invoice_ids:
    #                         unadjusted_credit = sum(unadjusted_invoice_ids.mapped('amount_residual_signed'))
    #
    #                 partners['outstanding_amt'] = abs(outstanding_amt)
    #                 partners['unadjusted_credit'] = abs(unadjusted_credit)
    #                 partners['gross_outstanding_amt'] = (partners['outstanding_amt'] - partners[
    #                     'unadjusted_credit']) if self.account_type == 'asset_receivable' else (
    #                         partners['outstanding_amt'] + partners['unadjusted_credit'])
    #                 partners['pdc_unmatured_amt'] = abs(pdc_unmatured_amt)
    #                 partners['settled_amt'] = partners['gross_outstanding_amt'] - partners['pdc_unmatured_amt']
    #                 partners['is_last_page_of_partner'] = True
    #
    #                 vals.append(partners)
    #
    #     if not vals:
    #         raise ValidationError("There is no data available in this date range !!")
    #
    #     company_bank = []
    #     if self.company_id.bank_ids:
    #         for bank in self.company_id.bank_ids:
    #             if bank.is_default:
    #                 company_bank.append({
    #                     'acc_name': bank.acc_holder_name,
    #                     'currency_id': bank.currency_id.name,
    #                     'bank_name': bank.bank_id.display_name,
    #                     'acc_number': bank.acc_number,
    #                     'iban_number': bank.bank_iban_number,
    #                     'swift_code': bank.bank_id.bic
    #                 })
    #
    #     data = {
    #         'company_logo': self.company_id.logo and image_data_uri(
    #             self.company_id.logo) if self.company_id.logo else '',
    #         'company_name': self.company_id.name,
    #         'company_zip': self.company_id.zip,
    #         'company_phone': self.company_id.phone,
    #         'company_mobile': self.company_id.mobile,
    #         'company_email': self.company_id.email,
    #         'company_website': self.company_id.website,
    #         'company_vat': self.company_id.vat,
    #         'company_city': self.company_id.city,
    #         'company_state': self.company_id.state_id.name,
    #         'company_country': self.company_id.country_id.code,
    #
    #         'date_to': self.date_to,
    #         'values': vals,
    #         'aging_values': aging_values,
    #         'company_bank': company_bank,
    #         'account_type': self.account_type,
    #     }
    #
    #     return self.env.ref('kg_voyage_marine_accounting.action_soa_report').with_context(
    #         landscape=False).report_action(self, data=data)
