# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


import xlsxwriter
from io import BytesIO
from datetime import date, datetime


try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes


class AccountCashBookReport(models.TransientModel):
    _name = "account.cashbook.report"
    _description = "Cash Book Report"

    def _get_default_account_ids(self):
        journals = self.env['account.journal'].search([('type', '=', 'cash')])
        accounts = []
        for journal in journals:
            if journal.default_account_id.id:
                accounts.append(journal.default_account_id.id)
            if journal.company_id.account_journal_payment_credit_account_id.id:
                accounts.append(journal.company_id.account_journal_payment_credit_account_id.id)
            if journal.company_id.account_journal_payment_debit_account_id.id:
                accounts.append(journal.company_id.account_journal_payment_debit_account_id.id)
            for acc_out in journal.outbound_payment_method_line_ids:
                if acc_out.payment_account_id:
                    accounts.append(acc_out.payment_account_id.id)
            for acc_in in journal.inbound_payment_method_line_ids:
                if acc_in.payment_account_id:
                    accounts.append(acc_in.payment_account_id.id)
        return accounts

    date_from = fields.Date(string='Start Date', default=date.today(), required=True)
    date_to = fields.Date(string='End Date', default=date.today(), required=True)
    target_move = fields.Selection([('posted', 'Posted Entries'),
                                    ('all', 'All Entries')], string='Target Moves', required=True,
                                   default='posted')
    journal_ids = fields.Many2many('account.journal', string='Journals', required=True,
                                   default=lambda self: self.env['account.journal'].search([]))
    account_ids = fields.Many2many('account.account', 'account_account_cashbook_report', 'report_line_id',
                                   'account_id', 'Accounts', default=_get_default_account_ids)

    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement')
    sortby = fields.Selection(
        [('sort_date', 'Date'), ('sort_journal_partner', 'Journal & Partner')],
        string='Sort by',
        required=True, default='sort_date')
    initial_balance = fields.Boolean(string='Include Initial Balances',
                                     help='If you selected date, this field allow you to add a row to'
                                          ' display the amount of debit/credit/balance that precedes '
                                          'the filter you\'ve set.')
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    @api.onchange('account_ids')
    def onchange_account_ids(self):
        if self.account_ids:
            journals = self.env['account.journal'].search(
                [('type', '=', 'cash')])
            accounts = []
            for journal in journals:
                accounts.append(journal.company_id.account_journal_payment_credit_account_id.id)
            domain = {'account_ids': [('id', 'in', accounts)]}
            return {'domain': domain}

    def _build_comparison_context(self, data):
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form'][
            'journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form'][
            'target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        return result

    def _get_account_move_entry(self, accounts, init_balance, sortby, display_account):

        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Prepare initial sql query and Get the initial move lines
        if init_balance:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=self.env.context.get('date_from'), date_to=False,initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
            sql = ("""
                    SELECT 0 AS lid,
                    l.account_id AS account_id, '' AS ldate, '' AS lcode,
                    0.0 AS amount_currency,'' AS lref,'Initial Balance' AS lname,
                    COALESCE(SUM(l.credit),0.0) AS credit,COALESCE(SUM(l.debit),0.0) AS debit,COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit),0) as balance,
                    '' AS lpartner_id,'' AS move_name, '' AS currency_code,NULL AS currency_id,'' AS partner_name,
                    '' AS mmove_id, '' AS invoice_id, '' AS invoice_type,'' AS invoice_number
                    FROM account_move_line l
                    LEFT JOIN account_move m ON (l.move_id = m.id)
                    LEFT JOIN res_currency c ON (l.currency_id = c.id)
                    LEFT JOIN res_partner p ON (l.partner_id = p.id)
                    JOIN account_journal j ON (l.journal_id = j.id)
                    JOIN account_account acc ON (l.account_id = acc.id)
                    WHERE l.account_id IN %s""" + filters + 'GROUP BY l.account_id')
            params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)

        sql_sort = 'l.date, l.move_id'
        if sortby == 'sort_journal_partner':
            sql_sort = 'j.code, p.name, l.move_id'

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
        if not accounts:
            journals = self.env['account.journal'].search([('type', '=', 'cash')])
            accounts = []
            for journal in journals:
                for acc_out in journal.outbound_payment_method_line_ids:
                    if acc_out.payment_account_id:
                        accounts.append(acc_out.payment_account_id.id)
                for acc_in in journal.inbound_payment_method_line_ids:
                    if acc_in.payment_account_id:
                        accounts.append(acc_in.payment_account_id.id)
            accounts = self.env['account.account'].search([('id', 'in', accounts)])

        sql = ('''SELECT l.id AS lid, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) AS balance,\
                          m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
                          FROM account_move_line l\
                          JOIN account_move m ON (l.move_id=m.id)\
                          LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                          LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                          JOIN account_journal j ON (l.journal_id=j.id)\
                          JOIN account_account acc ON (l.account_id = acc.id) \
                          WHERE l.account_id IN %s ''' + filters + ''' GROUP BY l.id, l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, p.name ORDER BY ''' + sql_sort)

        params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        for row in cr.dictfetchall():
            balance = 0
            for line in move_lines.get(row['account_id']):
                balance += line['debit'] - line['credit']
            row['balance'] += balance
            move_lines[row.pop('account_id')].append(row)

        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['move_lines'] = move_lines[account.id]
            for line in res.get('move_lines'):
                res['debit'] += line['debit']
                res['credit'] += line['credit']
                res['balance'] = line['balance']
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'movement' and res.get('move_lines'):
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(res['balance']):
                account_res.append(res)
        return account_res

    @api.model
    def _get_report_values(self, docids, data=None):
        model = data['res_model']
        docs = self.env[model].browse(self.env.context.get('docs_ids', []))
        init_balance = data['form'].get('initial_balance', True)
        display_account = data['form'].get('display_account')

        sortby = data['form'].get('sortby', 'sort_date')
        codes = []

        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]
            data['form']['codes']=codes
        account_ids = data['form']['account_ids']
        accounts = self.env['account.account'].search([('id', 'in', account_ids)])
        if not accounts:
            journals = self.env['account.journal'].search([('type', '=', 'cash')])
            accounts = []
            for journal in journals:
                for acc_out in journal.outbound_payment_method_line_ids:
                    if acc_out.payment_account_id:
                        accounts.append(acc_out.payment_account_id.id)
                for acc_in in journal.inbound_payment_method_line_ids:
                    if acc_in.payment_account_id:
                        accounts.append(acc_in.payment_account_id.id)
            accounts = self.env['account.account'].search([('id', 'in', accounts)])
        record = self.with_context(data['form'].get('comparison_context', {}))._get_account_move_entry(accounts,
                                                                                                       init_balance,
                                                                                                       sortby,
                                                                                                       display_account)
        return record

    def common_function(self):
        data = {}
        data['form'] = self.read(['target_move', 'date_from', 'date_to', 'journal_ids', 'account_ids',
                                  'sortby', 'initial_balance', 'display_account', ])[0]
        comparison_context = self._build_comparison_context(data)
        data['res_model'] = self._name
        test = self._get_report_values(self.ids, data)
        data['data'] = test
        data['form']['comparison_context'] = comparison_context
        return data

    def check_report(self):
        data= self.common_function()
        report_action = self.env.ref('kg_cash_book_report.action_cash_book').report_action(self, data=data)
        return report_action


    def print_xlsx(self):
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {
            # 'output_type': self.read()[0]['output_type'][0],
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }
        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)
        self.generate_xlsx_report(workbook=workbook, data=self.common_function())

        workbook.close()
        fout = encodebytes(file_io.getvalue())
        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'Cash Book'
        filename = '%s_%s' % (report_name, datetime_string)
        self.write({'fileout': fout, 'fileout_filename': filename})
        file_io.close()
        filename += '%2Exlsx'
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + filename,
        }


    def generate_xlsx_report(self, workbook, data):
        bold = workbook.add_format({'bold': True})
        # cs_grp_gs = workbook.add_format({'color': 'black', 'align': 'left'})
        # text_bold = workbook.add_format({'align': 'center', 'bold': True})
        reorder_sheet = workbook.add_worksheet("Cash Book")

        # Write headers
        headers = ['Date', 'JRNL', 'Partner', 'Ref', 'Move', 'Entry Label', 'Debit', 'Credit', 'Balance',
                   'Currency']
        for col, header in enumerate(headers):
            reorder_sheet.write(0, col, header, bold)

        # Write data
        row = 1
        for account in data['data']:
            # Write account info
            reorder_sheet.write(row, 0, account['code'] + ' ' + account['name'], bold)
            reorder_sheet.merge_range(row, 0, row, 5, account['code'] + ' ' + account['name'], bold)
            reorder_sheet.write(row, 6, account['debit'], bold)
            reorder_sheet.write(row, 7, account['credit'], bold)
            reorder_sheet.write(row, 8, account['balance'], bold)
            reorder_sheet.write(row, 9, account.get('currency_code', ''), bold)
            row += 1

            # Write move lines
            for line in account['move_lines']:
                reorder_sheet.write(row, 0, line['ldate'])
                reorder_sheet.write(row, 1, line['lcode'])
                reorder_sheet.write(row, 2, line['partner_name'])
                reorder_sheet.write(row, 3, line.get('lref', ''))
                reorder_sheet.write(row, 4, line['move_name'])
                reorder_sheet.write(row, 5, line['lname'])
                reorder_sheet.write(row, 6, line['debit'])
                reorder_sheet.write(row, 7, line['credit'])
                reorder_sheet.write(row, 8, line['balance'])
                reorder_sheet.write(row, 9, line.get('currency_code', ''))
                row += 1
