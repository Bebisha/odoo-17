from base64 import encodebytes
from datetime import date
from io import BytesIO

from odoo.exceptions import ValidationError
from odoo import models, fields, _

try:
    from odoo.tools.misc import xlsxwriter, DEFAULT_SERVER_DATETIME_FORMAT
except ImportError:
    import xlsxwriter


class AccountGeneralReportWizard(models.TransientModel):
    _name = "account.general.report.wizard"
    _description = "Account General Ledger Report"

    name = fields.Char(string="Reference")
    start_date = fields.Date(string="Start Date", default=date.today())
    end_date = fields.Date(string="End Date", default=date.today())
    account_ids = fields.Many2many("account.account", string="Accounts")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def button_print_pdf_report(self):
        if self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))

        vals = []

        domain = [('date', '>=', self.start_date), ('date', '<=', self.end_date), ('parent_state', '=', 'posted')]
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))

        aml_ids = self.env['account.move.line'].search(domain, order='date asc')

        if aml_ids:
            account_ids = aml_ids.mapped('account_id')
            for account in account_ids:
                ledger_moves = aml_ids.filtered(lambda x: x.account_id == account)
                print(ledger_moves,'ledgersssssssssssssssssssssssssss')
                opening_balance = sum(self.env['account.move.line'].search([
                    ('account_id', '=', account.id),
                    ('date', '<', self.start_date),
                    ('parent_state', '=', 'posted')
                ]).mapped('balance'))

                net_effect = sum(ledger_moves.mapped('balance'))
                closing_balance = opening_balance + net_effect

                account_info = {
                    'account_code': account.code,
                    'account_name': account.name.upper(),
                    'opening_balance': "{:.2f}".format(opening_balance),
                    'closing_balance': "{:.2f}".format(closing_balance),
                    'company_currency': self.company_id.currency_id.name,
                    'aml_details': []
                }

                running_balance = opening_balance
                for line in ledger_moves:
                    balance = line.debit - line.credit
                    running_balance += balance
                    if line.debit > 0 or line.credit > 0:
                        account_info['aml_details'].append({
                            'date': line.date,
                            'journal_entry': line.move_name,
                            'partner_id': line.partner_id.name,
                            'name': line.name,
                            'debit': "{:.2f}".format(line.debit),
                            'credit': "{:.2f}".format(line.credit),
                            'company_currency': self.company_id.currency_id.name,
                            'running_balance': "{:.2f}".format(running_balance)
                        })

                if account_info['aml_details']:
                    vals.append(account_info)

        if not vals:
            raise ValidationError(_('No data in this date range'))

        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'company_name': self.company_id.name,
            'company_zip': self.company_id.zip,
            'company_phone': self.company_id.phone,
            'company_mobile': self.company_id.mobile,
            'company_email': self.company_id.email,
            'company_website': self.company_id.website,
            'company_state': self.company_id.state_id.name,
            'company_country': self.company_id.country_id.code,
            'values': vals
        }

        return self.env.ref('kg_al_sharqiya_accounting.action_account_general_ledger_report_pdf').with_context(
            landscape=False).report_action(self, data=data)

    def button_view_report(self):
        if self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))
        vals = []

        domain = [('date', '>=', self.start_date), ('date', '<=', self.end_date), ('parent_state', '=', 'posted')]
        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))

        aml_ids = self.env['account.move.line'].search(domain, order='date asc')

        if aml_ids:
            account_ids = aml_ids.mapped('account_id')
            for account in account_ids:
                ledger_moves = aml_ids.filtered(lambda x: x.account_id == account)
                opening_balance = sum(self.env['account.move.line'].search([
                    ('account_id', '=', account.id),
                    ('date', '<', self.start_date),
                    ('parent_state', '=', 'posted')
                ]).mapped('balance'))

                net_effect = sum(ledger_moves.mapped('balance'))
                closing_balance = opening_balance + net_effect

                account_info = {
                    'account_code': account.code,
                    'account_name': account.name.upper(),
                    'opening_balance': "{:.2f}".format(opening_balance),
                    'closing_balance': "{:.2f}".format(closing_balance),
                    'company_currency': self.company_id.currency_id.name,
                    'aml_details': []
                }

                running_balance = opening_balance
                for line in ledger_moves:
                    balance = line.debit - line.credit
                    running_balance += balance
                    if line.debit > 0 or line.credit > 0:
                        account_info['aml_details'].append({
                            'date': line.date,
                            'journal_entry': line.move_name,
                            'partner_id': line.partner_id.name,
                            'name': line.name,
                            'debit': "{:.2f}".format(line.debit),
                            'credit': "{:.2f}".format(line.credit),
                            'company_currency': self.company_id.currency_id.name,
                            'running_balance': "{:.2f}".format(running_balance)
                        })

                if account_info['aml_details']:
                    vals.append(account_info)

        if not vals:
            raise ValidationError(_('No data in this date range'))

        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'company_name': self.company_id.name,
            'company_zip': self.company_id.zip,
            'company_phone': self.company_id.phone,
            'company_mobile': self.company_id.mobile,
            'company_email': self.company_id.email,
            'company_website': self.company_id.website,
            'company_state': self.company_id.state_id.name,
            'company_country': self.company_id.country_id.code,
            'values': vals
        }

        return self.env.ref('kg_al_sharqiya_accounting.action_account_general_ledger_report_html').with_context(
            landscape=False).report_action(self, data=data)

    def button_print_excel_report(self):
        if self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))

        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('parent_state', '=', 'posted'), ('company_id', '=', self.company_id.id)
        ]

        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))

        aml_id = self.env['account.move.line'].search(domain, order='date asc')

        if not aml_id:
            raise ValidationError(_('No data in this date range'))

        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {

            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_modeaccount.movel': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        report_name = 'Account General Ledger Report'
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        sheet = workbook.add_worksheet('Account General Ledger Report')

        style_specification_data_white_center = workbook.add_format()
        style_specification_data_white_center.set_fg_color('white')
        style_specification_data_white_center.set_font_name('Times New Roman')
        style_specification_data_white_center.set_bold()
        style_specification_data_white_center.set_text_wrap()
        style_specification_data_white_center.set_align('center')
        style_specification_data_white_center.set_border()

        style_specification_data_white_right = workbook.add_format()
        style_specification_data_white_right.set_fg_color('white')
        style_specification_data_white_right.set_font_name('Times New Roman')
        style_specification_data_white_right.set_bold()
        style_specification_data_white_right.set_text_wrap()
        style_specification_data_white_right.set_align('right')
        style_specification_data_white_right.set_border()

        style_specifications_white_left = workbook.add_format()
        style_specifications_white_left.set_fg_color('white')
        style_specifications_white_left.set_font_name('Times New Roman')
        style_specifications_white_left.set_bold()
        style_specifications_white_left.set_text_wrap()
        style_specifications_white_left.set_align('left')

        style_specifications_white_center = workbook.add_format()
        style_specifications_white_center.set_fg_color('white')
        style_specifications_white_center.set_font_name('Times New Roman')
        style_specifications_white_center.set_bold()
        style_specifications_white_center.set_text_wrap()
        style_specifications_white_center.set_align('center')
        style_specifications_white_center.set_font_color('#8A2BE2')

        style_specification_data_blue = workbook.add_format()
        style_specification_data_blue.set_fg_color('#9ACEEB')
        style_specification_data_blue.set_font_name('Times New Roman')
        style_specification_data_blue.set_bold()
        style_specification_data_blue.set_text_wrap()
        style_specification_data_blue.set_align('center')
        style_specification_data_blue.set_border()

        style_specification_data_brown = workbook.add_format()
        style_specification_data_brown.set_fg_color('#96e281')
        style_specification_data_brown.set_font_name('Times New Roman')
        style_specification_data_brown.set_bold()
        style_specification_data_brown.set_text_wrap()
        style_specification_data_brown.set_align('left')
        style_specification_data_brown.set_border()
        style_specification_data_brown.set_font_color('#800000')

        style_specification_data_orange = workbook.add_format()
        style_specification_data_orange.set_fg_color('#ffcc99')
        style_specification_data_orange.set_font_name('Times New Roman')
        style_specification_data_orange.set_bold()
        style_specification_data_orange.set_text_wrap()
        style_specification_data_orange.set_align('left')
        style_specification_data_orange.set_border()
        style_specification_data_orange.set_font_color('#333300')

        style_specification_data_pink = workbook.add_format()
        style_specification_data_pink.set_fg_color('#99ccff')
        style_specification_data_pink.set_font_name('Times New Roman')
        style_specification_data_pink.set_bold()
        style_specification_data_pink.set_text_wrap()
        style_specification_data_pink.set_align('left')
        style_specification_data_pink.set_border()
        style_specification_data_pink.set_font_color('#333300')

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 25)

        row = 0
        col = 0

        sheet.merge_range(row, col, row, col + 5, str(self.company_id.name),
                          style_specifications_white_left)

        row = row + 1
        address_parts = []

        if self.company_id.zip:
            address_parts.append("PO BOX : " + str(self.company_id.zip))
        if self.company_id.state_id:
            address_parts.append(str(self.company_id.state_id.name))
        if self.company_id.country_id:
            address_parts.append(str(self.company_id.country_id.name))

        address = ", ".join(address_parts) if address_parts else " "

        sheet.merge_range(row, col, row, col + 5, address, style_specifications_white_left)

        row = row + 1
        sheet.merge_range(row, col, row, col + 5, 'ACCOUNT GENERAL LEDGER REPORT',
                          style_specifications_white_center)

        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('parent_state', '=', 'posted'), ('company_id', '=', self.company_id.id)
        ]

        if self.account_ids:
            domain.append(('account_id', 'in', self.account_ids.ids))

        aml_id = self.env['account.move.line'].search(domain, order='date asc')

        if aml_id:
            account_id = aml_id.mapped('account_id')
            for acc in account_id:
                combined_account = f"{acc.code} {acc.name}"
                company_currency = self.company_id.currency_id.name

                ledger_move_id = aml_id.filtered(lambda x: x.account_id.id == acc.id)
                opening_entries = self.env['account.move.line'].search([
                    ('account_id', '=', acc.id),
                    ('date', '<', self.start_date),
                    ('parent_state', '=', 'posted'), ('company_id', '=', self.company_id.id)
                ])
                sum_opening_balance = sum(opening_entries.mapped('balance'))
                opening_balance = "{: .2f}".format(sum_opening_balance)

                net_effect = sum(aml_id.filtered(lambda x: x.account_id.id == acc.id).mapped('balance'))
                sum_closing_balance = sum_opening_balance + net_effect
                closing_balance = "{: .2f}".format(sum_closing_balance)

                combined_opening_balance = f"Opening Balance: {opening_balance} {company_currency}"
                combined_closing_balance = f"Closing Balance: {closing_balance} {company_currency}"

                row = row + 1
                col = col
                sheet.merge_range(row, col, row, col + 5, combined_account, style_specification_data_brown)

                row = row + 1
                col = col
                sheet.merge_range(row, col + 4, row, col + 5, combined_opening_balance, style_specification_data_orange)

                row = row + 1
                col = col
                header_row = row
                header_col = col
                sheet.write(header_row, header_col, 'Date', style_specification_data_blue)
                sheet.write(header_row, header_col + 1, 'Journal Entry', style_specification_data_blue)
                sheet.write(header_row, header_col + 2, 'Label', style_specification_data_blue)
                sheet.write(header_row, header_col + 3, 'Debit', style_specification_data_blue)
                sheet.write(header_row, header_col + 4, 'Credit', style_specification_data_blue)
                sheet.write(header_row, header_col + 5, 'Running Balance', style_specification_data_blue)

                row = row + 1
                col = col

                running_balance = 0
                count = 0
                for line in ledger_move_id:
                    count += 1
                    balance = line.debit - line.credit
                    if count == 1:
                        running_balance = balance + sum_opening_balance
                    else:
                        running_balance += balance

                    debit = "{: .2f}".format(line.debit)
                    credit = "{: .2f}".format(line.credit)
                    total_running_balance = "{: .2f}".format(running_balance)
                    combined_debit = f"{debit} {company_currency}"
                    combined_credit = f"{credit} {company_currency}"
                    combined_running_balance = f"{total_running_balance} {company_currency}"

                    if line.debit > 0 or line.credit > 0:
                        sheet.write(row, col, str(line.date), style_specification_data_white_center)
                        sheet.write(row, col + 1, line.move_name, style_specification_data_white_center)
                        sheet.write(row, col + 2, line.name, style_specification_data_white_center)
                        sheet.write(row, col + 3, combined_debit, style_specification_data_white_right)
                        sheet.write(row, col + 4, combined_credit, style_specification_data_white_right)
                        sheet.write(row, col + 5, combined_running_balance, style_specification_data_white_right)

                        row = row + 1
                        col = col

                row = row
                col = col
                sheet.merge_range(row, col + 4, row, col + 5, combined_closing_balance,
                                  style_specification_data_pink)

                row = row + 1
                col = col
