from base64 import encodebytes
from collections import defaultdict
from datetime import date, datetime
from io import BytesIO

from odoo.exceptions import ValidationError
from odoo import models, fields, _

try:
    from odoo.tools.misc import xlsxwriter, DEFAULT_SERVER_DATETIME_FORMAT
except ImportError:
    import xlsxwriter


class AccountGeneralReportWizard(models.TransientModel):
    _name = "trail.balance.report.wizard"
    _description = "Account Trail Balance Report"

    name = fields.Char(string="Reference")
    start_date = fields.Date(string="Start Date", default=date.today())
    end_date = fields.Date(string="End Date", default=date.today())
    # account_ids = fields.Many2many("account.account", string="Accounts")
    tag_id = fields.Many2one("account.account.tag", string="Tag", )
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def get_data(self):
        """fetching data for report"""
        if self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))

        vals = []
        domain = []

        account_ids = self.env['account.account'].search(domain, order='code asc')
        tags = account_ids.mapped('tag_ids')

        tag_to_accounts = defaultdict(list)
        tags = tags.filtered(lambda t: t.is_trial_balance)
        if self.tag_id:
            tags = self.tag_id

        for tag in tags:
            tag_id_set = set(tag.ids)

            matching_accounts = account_ids.filtered(lambda x: bool(tag_id_set & set(x.tag_ids.ids)))

            if matching_accounts:
                tag_account_info = []

                for account in matching_accounts:
                    # Get opening balance
                    opening_balance = sum(self.env['account.move.line'].search([
                        ('account_id', '=', account.id),
                        ('date', '<', self.start_date),
                        ('parent_state', '=', 'posted')
                    ]).mapped('balance'))

                    ledger_moves = self.env['account.move.line'].search([
                        ('account_id', '=', account.id),
                        ('date', '>=', self.start_date),
                        ('date', '<=', self.end_date),
                        ('parent_state', '=', 'posted')
                    ])

                    # Calculate net effect
                    net_effect = sum(ledger_moves.mapped('balance'))
                    debit = sum(ledger_moves.mapped('debit'))
                    credit = sum(ledger_moves.mapped('credit'))
                    balance = debit - credit
                    closing_balance = opening_balance + net_effect
                    credit_close = 0
                    debit_close = 0

                    if closing_balance < 0:
                        credit_close = abs(closing_balance)

                    else:
                        debit_close = closing_balance

                    # Prepare account info
                    account_info = {
                        'account_code': account.code,
                        'account_name': account.name.upper(),
                        'txn_balance': balance,
                        'opening_balance': opening_balance,
                        'closing_balance': closing_balance,
                        'debit': debit,
                        'credit': credit,
                        'closing_credit': credit_close,
                        'closing_debit': debit_close,
                        'company_currency': self.company_id.currency_id.name,
                        # 'aml_details': []  # Uncomment if you have details to include
                    }

                    # Append account info to tag_account_info
                    tag_account_info.append(account_info)

                tag_to_accounts[tag.name] = tag_account_info
            else:
                raise ValidationError(_('No Accounts Found'))

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
            'values': tag_to_accounts,
            'tag_name': self.tag_id.name if self.tag_id else False,
        }
        return data

    def button_print_pdf_report(self):
        """Button to print pdf report"""
        data = self.get_data()
        return self.env.ref('kg_al_sharqiya_accounting.action_trail_balance_report_pdf').with_context(
            landscape=False).report_action(self, data=data)

    def button_view_report(self):
        """Button to view the report"""
        data = self.get_data()
        return self.env.ref('kg_al_sharqiya_accounting.action_trail_balance_report_html').with_context(
            landscape=False).report_action(self, data=data)

    def button_print_excel_report(self):

        """To print xlsx Report"""
        self.get_data()

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

        report_name = 'Trial Balance Report'
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        """Generate XLSX Report"""
        sheet = workbook.add_worksheet('Trial Balance Report')
        data = self.get_data()

        # Define styles
        style_specifications_white_left = workbook.add_format({
            'bold': True,
            'font_name': 'Times New Roman',
            'align': 'left',
            'text_wrap': True
        })

        style_specifications_white_center = workbook.add_format({
            'bold': True,
            'font_name': 'Times New Roman',
            'align': 'center',
            'text_wrap': True,
            'font_color': '#8A2BE2'
        })

        style_specification_data_blue = workbook.add_format({
            'bold': True,
            'font_name': 'Times New Roman',
            'align': 'center',
            'text_wrap': True,
            'fg_color': '#9ACEEB',
            'border': 1
        })

        style_specification_data_white_right = workbook.add_format({
            'font_name': 'Times New Roman',
            'align': 'right',
            'border': 1
        })
        style_specification_data_white_right_bold = workbook.add_format({
            'font_name': 'Times New Roman',
            'align': 'right',
            'border': 1,
            'bold': True
        })

        style_specification_data_white_left = workbook.add_format({
            'font_name': 'Times New Roman',
            'align': 'left',
            'border': 1
        })
        style_specification_data_white_left_bold = workbook.add_format({
            'bold': True,
            'font_name': 'Times New Roman',
            'align': 'left',
            'border': 1
        })

        # Set column widths
        sheet.set_column(0, 0, 15)  # Account No.
        sheet.set_column(1, 1, 31)  # Account Name
        sheet.set_column(2, 2, 20)  # Opening Balance
        sheet.set_column(3, 3, 20)  # Txn Debit
        sheet.set_column(4, 4, 20)  # Txn Credit
        sheet.set_column(5, 5, 20)  # Closing Balance
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)

        row = 0
        col = 0
        sheet.merge_range(row, col, row, col + 5, data.get('company_name', ''), style_specifications_white_left)

        row += 1
        address_parts = []
        if data.get('company_zip'):
            address_parts.append(f"PO BOX: {data['company_zip']}")
        if data.get('company_state'):
            address_parts.append(data['company_state'])
        if data.get('company_country'):
            address_parts.append(data['company_country'])

        address = ", ".join(address_parts) if address_parts else " "
        sheet.merge_range(row, col, row, col + 5, address, style_specifications_white_left)

        row += 1
        sheet.merge_range(row, col, row, col + 5, 'TRIAL BALANCE REPORT', style_specifications_white_center)

        row += 1
        sheet.merge_range(row, col, row, col + 5,
                          f"FROM {data['start_date'].strftime('%d/%m/%Y')} TO {data['end_date'].strftime('%d/%m/%Y')}",
                          style_specifications_white_center)

        row += 1
        sheet.write(row, col, 'Account NO.', style_specification_data_blue)
        sheet.write(row, col + 1, 'Account Name', style_specification_data_blue)
        sheet.write(row, col + 2, 'Opening Balance', style_specification_data_blue)
        sheet.write(row, col + 3, 'Txn Debit', style_specification_data_blue)
        sheet.write(row, col + 4, 'Txn Credit', style_specification_data_blue)
        sheet.write(row, col + 5, 'Txn Balance', style_specification_data_blue)
        sheet.write(row, col + 6, 'Closing Debit', style_specification_data_blue)
        sheet.write(row, col + 7, 'Closing Credit', style_specification_data_blue)
        sheet.write(row, col + 8, 'Closing Balance', style_specification_data_blue)

        total_opening_balance = 0
        total_debit = 0
        total_credit = 0
        total_closing_balance = 0
        total_txn_balance = 0
        total_closing_credit = 0
        total_closing_debit = 0

        for tag, entries in data.get('values', {}).items():
            row += 1
            sheet.merge_range(row, col, row, col + 8, tag, style_specifications_white_left)
            for entry in entries:
                row += 1
                sheet.write(row, col, entry['account_code'], style_specification_data_white_left)
                sheet.write(row, col + 1, entry['account_name'], style_specification_data_white_left)
                sheet.write(row, col + 2, "%.2f" % entry['opening_balance'], style_specification_data_white_right)
                sheet.write(row, col + 3, "%.2f" % entry['debit'], style_specification_data_white_right)
                sheet.write(row, col + 4, "%.2f" % entry['credit'], style_specification_data_white_right)
                sheet.write(row, col + 5, "%.2f" % entry['txn_balance'], style_specification_data_white_right)
                sheet.write(row, col + 6, "%.2f" % entry['closing_debit'], style_specification_data_white_right)
                sheet.write(row, col + 7, "%.2f" % entry['closing_credit'], style_specification_data_white_right)
                sheet.write(row, col + 8, "%.2f" % entry['closing_balance'], style_specification_data_white_right)

                total_opening_balance += entry['opening_balance']
                total_debit += entry['debit']
                total_credit += entry['credit']
                total_closing_balance += entry['closing_balance']
                total_txn_balance += entry['txn_balance']
                total_closing_credit += entry['closing_credit']
                total_closing_debit += entry['closing_debit']

        row += 1
        sheet.merge_range(row, col, row, col + 1, 'Total', style_specification_data_white_left_bold)
        sheet.write(row, col + 2, "%.2f" % total_opening_balance, style_specification_data_white_right_bold)
        sheet.write(row, col + 3, "%.2f" % total_debit, style_specification_data_white_right_bold)
        sheet.write(row, col + 4, "%.2f" % total_credit, style_specification_data_white_right_bold)
        sheet.write(row, col + 5, "%.2f" % total_txn_balance, style_specification_data_white_right_bold)
        sheet.write(row, col + 6, "%.2f" % total_closing_debit, style_specification_data_white_right_bold)
        sheet.write(row, col + 7, "%.2f" % total_closing_credit, style_specification_data_white_right_bold)
        sheet.write(row, col + 8, "%.2f" % total_closing_balance, style_specification_data_white_right_bold)

        row += 2
