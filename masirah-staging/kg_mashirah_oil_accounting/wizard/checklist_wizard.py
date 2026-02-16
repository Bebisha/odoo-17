from odoo import models, fields, _
from odoo.exceptions import ValidationError
from base64 import encodebytes
from io import BytesIO
import xlsxwriter


class KGChecklistWizard(models.TransientModel):
    _name = "kg.checklist.wizard"
    _description = "Checklist Wizard"

    name = fields.Char(string="Reference")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def button_checklist_report(self):
        if self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))

        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {

            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_modestock.movel': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        start_date = self.start_date.strftime("%d/%m/%Y")
        end_date = self.end_date.strftime("%d/%m/%Y")

        report_name = 'TAX Checklist Report ' + str(start_date) + ' - ' + str(end_date)
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        style_specification_data_white_left = workbook.add_format()
        style_specification_data_white_left.set_fg_color('white')
        style_specification_data_white_left.set_font_name('Times New Roman')
        style_specification_data_white_left.set_font_size('8')
        style_specification_data_white_left.set_align('left')
        style_specification_data_white_left.set_border()
        style_specification_data_white_left.set_text_wrap()

        style_specification_data_white_right = workbook.add_format()
        style_specification_data_white_right.set_fg_color('white')
        style_specification_data_white_right.set_font_name('Times New Roman')
        style_specification_data_white_right.set_font_size('8')
        style_specification_data_white_right.set_align('right')
        style_specification_data_white_right.set_border()
        style_specification_data_white_right.set_text_wrap()

        style_specification_data_white_center = workbook.add_format()
        style_specification_data_white_center.set_fg_color('white')
        style_specification_data_white_center.set_font_name('Times New Roman')
        style_specification_data_white_center.set_font_size('8')
        style_specification_data_white_center.set_align('center')
        style_specification_data_white_center.set_border()
        style_specification_data_white_center.set_text_wrap()

        style_specification_data_brown = workbook.add_format()
        style_specification_data_brown.set_fg_color('white')
        style_specification_data_brown.set_font_name('Times New Roman')
        style_specification_data_brown.set_font_size('8')
        style_specification_data_brown.set_align('left')
        style_specification_data_brown.set_border()
        style_specification_data_brown.set_font_color('#800000')
        style_specification_data_brown.set_fg_color('#ffe6cc')
        style_specification_data_brown.set_text_wrap()

        start_date = self.start_date.strftime("%d/%m/%Y")
        end_date = self.end_date.strftime("%d/%m/%Y")

        tax_tag = self.env['account.account.tag'].search([])
        tax_tag_name = tax_tag.mapped('name')

        #################################################################################################

        sheet = workbook.add_worksheet('Std Rated Sales - Box 1(a)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 40)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)

        tag_1a = [item for item in tax_tag_name if ('+1(a)' in item or '-1(a)' in item) and 'Tax' in item]
        if tag_1a:
            aml_1a_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_1a)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 10,
                              'Supplies of goods / services taxed at 5% - Box 1(a)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Tax Invoice/Tax Credit Note #', style_specification_data_brown)
            sheet.write(row, col + 4, 'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Tax Invoice/Tax credit note Amount OMR (before VAT)',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'VAT Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 8, 'Customer Name', style_specification_data_brown)
            sheet.write(row, col + 9, 'Customer VATIN', style_specification_data_brown)
            sheet.write(row, col + 10, 'Clear description of the supply', style_specification_data_brown)

            row = row + 1
            col = col
            serial_a1 = 1

            total_base_amount = 0.00
            total_vat_amount = 0.00

            if aml_1a_ids:
                for a1 in aml_1a_ids:
                    sheet.write(row, col, serial_a1, style_specification_data_white_center)
                    sheet.write(row, col + 1, a1.company_id.vat if a1.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, a1.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, a1.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, a1.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, "{: .2f}".format(a1.tax_base_amount) + ' ' + str(a1.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 7,
                                "{: .2f}".format(abs(a1.balance)) + ' ' + str(a1.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 8, a1.partner_id.name, style_specification_data_white_left)
                    sheet.write(row, col + 9, a1.partner_id.vat if a1.partner_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 10, a1.name, style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_a1 += 1

                    total_base_amount += a1.tax_base_amount
                    total_vat_amount += abs(a1.balance)

            row = row
            col = col

            sheet.write(row, col + 5, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 6,
                        "{: .2f}".format(total_base_amount) + ' ' + str(self.company_id.currency_id.name),
                        style_specification_data_white_right)
            sheet.write(row, col + 7,
                        "{: .2f}".format(total_vat_amount) + ' ' + str(self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 10,
                              'Total value of standard rated supplies of goods and services in the Sultanate, including deemed supplies.',
                              style_specification_data_white_left)

        #########################################################################

        sheet = workbook.add_worksheet('Zero Rated Sales - Box 1(b)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 40)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)
        sheet.set_column(11, 11, 35)

        tag_1b = [item for item in tax_tag_name if ('+1(b)' in item or '-1(b)' in item) and 'Tax' in item]
        if tag_1b:
            aml_1b_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_1b)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 11,
                              'Supplies of goods / services taxed at 0% - Box 1(b)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Tax Invoice/Tax Credit Note #', style_specification_data_brown)
            sheet.write(row, col + 4, 'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Tax Invoice/Tax credit note Amount OMR (before VAT)',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'Customer Name', style_specification_data_brown)
            sheet.write(row, col + 8, 'Customer VATIN', style_specification_data_brown)
            sheet.write(row, col + 9, 'Customer Country', style_specification_data_brown)
            sheet.write(row, col + 10, 'Clear description of the supply', style_specification_data_brown)
            sheet.write(row, col + 11, 'VAT Adjustments (if any)', style_specification_data_brown)

            row = row + 1
            col = col
            serial_b1 = 1
            total_b1_base_amount = 0.00

            if aml_1b_ids:
                for b1 in aml_1b_ids:
                    sheet.write(row, col, serial_b1, style_specification_data_white_center)
                    sheet.write(row, col + 1, b1.company_id.vat if b1.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, b1.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, b1.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, b1.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, "{: .2f}".format(b1.tax_base_amount) + ' ' + str(b1.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 7, b1.partner_id.name, style_specification_data_white_left)
                    sheet.write(row, col + 8, b1.partner_id.vat if b1.partner_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 9, b1.partner_id.country_id.name if b1.partner_id.country_id.name else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 10, b1.name, style_specification_data_white_left)
                    sheet.write(row, col + 11, '', style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_b1 += 1
                    total_b1_base_amount += b1.tax_base_amount

            row = row
            col = col

            sheet.write(row, col + 5, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 6,
                        "{: .2f}".format(total_b1_base_amount) + ' ' + str(self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 11,
                              'Total value of zero-rated supplies of goods and services in the Sultanate, excluding exports of goods or services.',
                              style_specification_data_white_left)

        ##############################################################################

        sheet = workbook.add_worksheet('Exempt Supplies - Box 1(c)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 50)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)
        sheet.set_column(11, 11, 35)

        tag_1c = [item for item in tax_tag_name if ('+1(c)' in item or '-1(c)' in item) and 'Tax' in item]
        if tag_1c:
            aml_1c_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_1c)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 11,
                              'Supplies of goods / services tax exempt - Box 1(c)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Tax Invoice/Tax Credit Note #', style_specification_data_brown)
            sheet.write(row, col + 4, 'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Tax Invoice/Tax credit note Amount OMR ',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'Customer Name', style_specification_data_brown)
            sheet.write(row, col + 8, 'Customer VATIN', style_specification_data_brown)
            sheet.write(row, col + 9, 'Customer Country', style_specification_data_brown)
            sheet.write(row, col + 10, 'Clear description of the supply', style_specification_data_brown)
            sheet.write(row, col + 11, 'VAT Adjustments (if any)', style_specification_data_brown)

            row = row + 1
            col = col
            serial_c1 = 1
            total_c1_balance = 0.00

            if aml_1c_ids:
                for c1 in aml_1c_ids:
                    sheet.write(row, col, serial_c1, style_specification_data_white_center)
                    sheet.write(row, col + 1, c1.company_id.vat if c1.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, c1.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, c1.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, c1.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6,
                                "{: .2f}".format(abs(c1.balance)) + ' ' + str(c1.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 7, c1.partner_id.name, style_specification_data_white_left)
                    sheet.write(row, col + 8, c1.partner_id.vat if c1.partner_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 9, c1.partner_id.country_id.name if c1.partner_id.country_id.name else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 10, c1.name, style_specification_data_white_left)
                    sheet.write(row, col + 11, ' ', style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_c1 += 1
                    total_c1_balance += abs(c1.balance)

            row = row
            col = col

            sheet.write(row, col + 5, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 6,
                        "{: .2f}".format(total_c1_balance) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 11,
                              'Total value of exempt supplies of goods and services in the Sultanate.  Excludes any out of scope supplies',
                              style_specification_data_white_left)

        #######################################################################

        sheet = workbook.add_worksheet('Profit Margin Sales - Box 1(f)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 50)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)
        sheet.set_column(11, 11, 35)
        sheet.set_column(12, 12, 35)
        sheet.set_column(13, 13, 35)

        tag_1f = [item for item in tax_tag_name if ('+1(f)' in item or '-1(f)' in item) and 'Tax' in item]
        if tag_1f:
            aml_1f_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_1f)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 13,
                              'Supply of goods as per profit margin scheme - Box 1(f)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Tax Invoice/Tax Credit Note #', style_specification_data_brown)
            sheet.write(row, col + 4, 'Tax Invoice/Tax credit note Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Profit Margin Self-Invoice Number',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'Cost of Purchase', style_specification_data_brown)
            sheet.write(row, col + 8, 'Tax Invoice/Tax credit note Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 9, 'Gross Profit Margin', style_specification_data_brown)
            sheet.write(row, col + 10, 'VAT-exclusive Profit Margin', style_specification_data_brown)
            sheet.write(row, col + 11, 'VAT Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 12, 'Customer Name', style_specification_data_brown)
            sheet.write(row, col + 13, 'Clear description of the used goods supply', style_specification_data_brown)

            row = row + 1
            col = col

            serial_f1 = 1
            total_f1_balance = 0.00

            if aml_1f_ids:
                for f1 in aml_1f_ids:
                    sheet.write(row, col, serial_f1, style_specification_data_white_center)
                    sheet.write(row, col + 1, f1.company_id.vat if f1.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, f1.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, f1.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, f1.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, ' ',
                                style_specification_data_white_left)
                    sheet.write(row, col + 7, ' ', style_specification_data_white_left)
                    sheet.write(row, col + 8,
                                "{: .2f}".format(abs(f1.balance)) + ' ' + str(f1.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 9, ' ', style_specification_data_white_left)
                    sheet.write(row, col + 10, ' ', style_specification_data_white_left)
                    sheet.write(row, col + 11,
                                "{: .2f}".format(abs(f1.balance)) + ' ' + str(f1.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 12, f1.partner_id.name, style_specification_data_white_left)
                    sheet.write(row, col + 13, ' ',
                                style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_f1 += 1
                    total_f1_balance += abs(f1.balance)

            row = row
            col = col

            sheet.write(row, col + 7, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 8,
                        "{: .2f}".format(total_f1_balance) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)
            sheet.write(row, col + 11,
                        "{: .2f}".format(total_f1_balance) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 13,
                              'Total profit margin for any supplies of goods as per profit margin scheme',
                              style_specification_data_white_left)

        #########################################################################################

        sheet = workbook.add_worksheet('RCM Purchases - Box 2(b)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 30)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 25)
        sheet.set_column(10, 10, 25)
        sheet.set_column(11, 11, 35)
        sheet.set_column(12, 12, 35)
        sheet.set_column(13, 13, 35)
        sheet.set_column(14, 14, 45)

        tag_2b = [item for item in tax_tag_name if ('+2(b)' in item or '-2(b)' in item) and 'Tax' in item]
        if tag_2b:
            aml_2b_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_2b)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 14,
                              'Purchases from outside of GCC subject to Reverse Charge Mechanism - Box 2(b)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Supplier Tax Invoice/Tax Credit Note No', style_specification_data_brown)
            sheet.write(row, col + 4, 'Invoice/ credit note Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Invoice/Credit Note Amount Foreign Currency',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'Currency symbol', style_specification_data_brown)
            sheet.write(row, col + 8, 'Exchange rate used', style_specification_data_brown)
            sheet.write(row, col + 9, 'Invoice/credit note Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 10, 'Reverse Charge VAT Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 11, 'Supplier Name', style_specification_data_brown)
            sheet.write(row, col + 12, 'Supplier Country', style_specification_data_brown)
            sheet.write(row, col + 13, 'Clear description of the transaction', style_specification_data_brown)
            sheet.write(row, col + 14, 'Deductible Reverse Charge VAT Amount OMR [to Box 6(a)]',
                        style_specification_data_brown)

            row = row + 1
            col = col

            serial_b2 = 1
            total_b2_tax_base_amount = 0.00

            if aml_2b_ids:
                for b2 in aml_2b_ids:
                    sheet.write(row, col, serial_b2, style_specification_data_white_center)
                    sheet.write(row, col + 1, b2.company_id.vat if b2.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, b2.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, b2.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, b2.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, b2.currency_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 7, b2.currency_id.symbol, style_specification_data_white_center)
                    sheet.write(row, col + 8,
                                "{: .2f}".format(b2.currency_rate),
                                style_specification_data_white_right)
                    sheet.write(row, col + 9,
                                "{: .2f}".format(abs(b2.tax_base_amount)) + ' ' + str(b2.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 10, ' ', style_specification_data_white_left)
                    sheet.write(row, col + 11, b2.partner_id.name,
                                style_specification_data_white_left)
                    sheet.write(row, col + 12, b2.partner_id.country_id.name if b2.partner_id.country_id.name else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 13, b2.name,
                                style_specification_data_white_left)
                    sheet.write(row, col + 14, ' ',
                                style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_b2 += 1
                    total_b2_tax_base_amount += abs(b2.tax_base_amount)

            row = row
            col = col

            sheet.write(row, col + 8, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 9,
                        "{: .2f}".format(total_b2_tax_base_amount) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 14,
                              'Total value of standard rated supplies received, which are subject to Reverse Charge Mechanism',
                              style_specification_data_white_left)

        ####################################################################################

        sheet = workbook.add_worksheet('Exports - Box 3(a)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 50)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)
        sheet.set_column(11, 11, 35)

        tag_3a = [item for item in tax_tag_name if ('+3(a)' in item or '-3(a)' in item) and 'Tax' in item]
        if tag_3a:
            aml_3a_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_3a)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 11,
                              'Exports of Goods and Services - Box 3(a)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Supplier Tax Invoice/Tax Credit Note No', style_specification_data_brown)
            sheet.write(row, col + 4, 'Invoice/ credit note Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Tax Invoice/Tax credit note Amount OMR (before VAT)',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'Customer Name', style_specification_data_brown)
            sheet.write(row, col + 8, 'Customer VATIN', style_specification_data_brown)
            sheet.write(row, col + 9, 'Customer Country', style_specification_data_brown)
            sheet.write(row, col + 10, 'Clear description of the supply', style_specification_data_brown)
            sheet.write(row, col + 11, 'VAT Adjustments (if any)', style_specification_data_brown)

            row = row + 1
            col = col

            serial_a3 = 1
            total_a3_tax_base_amount = 0.00

            if aml_3a_ids:
                for a3 in aml_3a_ids:
                    sheet.write(row, col, serial_a3, style_specification_data_white_center)
                    sheet.write(row, col + 1, a3.company_id.vat if a3.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, a3.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, a3.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, a3.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, "{: .2f}".format(a3.tax_base_amount) + ' ' + str(a3.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 7, a3.partner_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 8, a3.partner_id.vat if a3.partner_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 9, a3.partner_id.country_id.name if a3.partner_id.country_id.name else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 10, a3.name, style_specification_data_white_left)
                    sheet.write(row, col + 11, '',
                                style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_a3 += 1
                    total_a3_tax_base_amount += a3.tax_base_amount

            row = row
            col = col

            sheet.write(row, col + 5, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 6,
                        "{: .2f}".format(total_a3_tax_base_amount) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 11,
                              'Total value of supplies of goods and services exported on which zero rating for exportation applies. Excludes any out of scope supplies.',
                              style_specification_data_white_left)

        ######################################################################################3

        sheet = workbook.add_worksheet('Deferred Import - Box 4(a)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 50)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)
        sheet.set_column(11, 11, 35)
        sheet.set_column(12, 12, 35)
        sheet.set_column(13, 13, 35)

        tag_4a = [item for item in tax_tag_name if ('+4(a)' in item or '-4(a)' in item) and 'Tax' in item]
        if tag_4a:
            aml_4a_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_4a)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 13,
                              'Import of Goods (Postponed payment) - BOX 4(a)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Company Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Invoice # / Document #', style_specification_data_brown)
            sheet.write(row, col + 4, 'Invoice/ Document Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Invoice Amount OMR (before VAT)',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'VAT Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 8, 'Supplier Name', style_specification_data_brown)
            sheet.write(row, col + 9, 'Supplier Country', style_specification_data_brown)
            sheet.write(row, col + 10, 'Taxable amount to be reported on VAT return Box 4(a)',
                        style_specification_data_brown)
            sheet.write(row, col + 11, 'Customs Declaration Number', style_specification_data_brown)
            sheet.write(row, col + 12, 'Clear description of the goods imported', style_specification_data_brown)
            sheet.write(row, col + 13, 'Deductible VAT OMR Box 6(b)', style_specification_data_brown)

            row = row + 1
            col = col
            serial_a4 = 1
            total_a4_base_amount = 0.00
            total_a4_balance = 0.00

            if aml_4a_ids:
                for a4 in aml_4a_ids:
                    sheet.write(row, col, serial_a4, style_specification_data_white_center)
                    sheet.write(row, col + 1, a4.company_id.vat if a4.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, a4.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, a4.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, a4.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, "{: .2f}".format(a4.tax_base_amount) + ' ' + str(a4.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 7,
                                "{: .2f}".format(abs(a4.balance)) + ' ' + str(a4.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 8, a4.partner_id.name, style_specification_data_white_left)
                    sheet.write(row, col + 9, a4.partner_id.country_id.name if a4.partner_id.country_id.name else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 10, '',
                                style_specification_data_white_left)
                    sheet.write(row, col + 11, '', style_specification_data_white_left)
                    sheet.write(row, col + 12, '',
                                style_specification_data_white_left)
                    sheet.write(row, col + 13, '', style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_a4 += 1
                    total_a4_base_amount += a4.tax_base_amount
                    total_a4_balance += abs(a4.balance)

            row = row
            col = col

            sheet.write(row, col + 5, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 6,
                        "{: .2f}".format(total_a4_base_amount) + ' ' + str(self.company_id.currency_id.name),
                        style_specification_data_white_right)
            sheet.write(row, col + 7,
                        "{: .2f}".format(total_a4_balance) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 13,
                              'Total value of goods imported (excluding VAT) where VAT was postponed on import',
                              style_specification_data_white_left)

        #########################################################################################################

        sheet = workbook.add_worksheet('Goods Import - Box 4(b)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 50)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)
        sheet.set_column(11, 11, 35)
        sheet.set_column(12, 12, 35)

        tag_4b = [item for item in tax_tag_name if ('+4(b)' in item or '-4(b)' in item) and 'Tax' in item]
        if tag_4b:
            aml_4b_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_4b)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 12,
                              'Total goods imported - BOXES 4(b)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Tax Invoice/Tax Credit Note #', style_specification_data_brown)
            sheet.write(row, col + 4, 'Tax Invoice/Tax Credit Note Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Tax Invoice/Tax credit note Received Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'Tax Invoice/Tax credit note Amount OMR (before VAT)',
                        style_specification_data_brown)
            sheet.write(row, col + 8, 'VAT Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 9, 'VAT Amount Claimed OMR', style_specification_data_brown)
            sheet.write(row, col + 10, 'Supplier Name',
                        style_specification_data_brown)
            sheet.write(row, col + 11, 'Supplier VATIN', style_specification_data_brown)
            sheet.write(row, col + 12, 'Clear description of the supply', style_specification_data_brown)

            row = row + 1
            col = col
            serial_b4 = 1
            total_b4_base_amount = 0.00
            total_b4_balance = 0.00

            if aml_4b_ids:
                for b4 in aml_4b_ids:
                    sheet.write(row, col, serial_b4, style_specification_data_white_center)
                    sheet.write(row, col + 1, b4.company_id.vat if b4.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, b4.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, b4.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, b4.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, b4.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 7,
                                "{: .2f}".format(b4.tax_base_amount) + ' ' + str(b4.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 8,
                                "{: .2f}".format(abs(b4.balance)) + ' ' + str(b4.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 9, '', style_specification_data_white_left)
                    sheet.write(row, col + 10, b4.partner_id.name,
                                style_specification_data_white_left)
                    sheet.write(row, col + 11, b4.partner_id.vat if b4.partner_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 12, b4.name, style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_b4 += 1

                    total_b4_base_amount += b4.tax_base_amount
                    total_b4_balance += abs(b4.balance)

            row = row
            col = col

            sheet.write(row, col + 6, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 7,
                        "{: .2f}".format(total_b4_base_amount) + ' ' + str(self.company_id.currency_id.name),
                        style_specification_data_white_right)
            sheet.write(row, col + 8,
                        "{: .2f}".format(total_b4_balance) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 12,
                              'Total value of all purchases including exempt/standard/zero rated purchases and reverse charge purchases. Excludes imported goods, out of scope expenses and purchases of fixed (capital) assets.',
                              style_specification_data_white_left)

        #################################################################################

        sheet = workbook.add_worksheet('Output Adjustments - Box 5(b)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 50)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 40)

        tag_5b = [item for item in tax_tag_name if ('+5(b)' in item or '-5(b)' in item) and 'Tax' in item]
        if tag_5b:
            aml_5b_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_5b)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 8,
                              'Adjustment of VAT due - Box 5(b)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Company Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 4, 'Tax Invoice/Tax Credit Note # (if applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Transaction / Adjustment Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'VAT Adjustment Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 8, 'Clear description of the adjustment', style_specification_data_brown)

            row = row + 1
            col = col
            serial_b5 = 1
            total_b5_balance = 0.00

            if aml_5b_ids:
                for b5 in aml_5b_ids:
                    sheet.write(row, col, serial_b5, style_specification_data_white_center)
                    sheet.write(row, col + 1, b5.company_id.vat if b5.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, b5.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, b5.partner_id.name,
                                style_specification_data_white_left)
                    sheet.write(row, col + 4, b5.move_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, b5.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 7,
                                "{: .2f}".format(abs(b5.balance)) + ' ' + str(b5.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 8, b5.name, style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_b5 += 1
                    total_b5_balance += abs(b5.balance)

            row = row
            col = col

            sheet.write(row, col + 6, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 7,
                        "{: .2f}".format(total_b5_balance) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 8,
                              'Any adjustments to Output VAT due that must be declared in this period including bad debts related to standard rated supplies, refunds, returns, and any other adjustments affecting VAT due',
                              style_specification_data_white_left)

        ###########################################################################################

        sheet = workbook.add_worksheet('Input - Tax 6(a)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 30)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 35)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)
        sheet.set_column(11, 11, 35)
        sheet.set_column(12, 12, 35)
        sheet.set_column(13, 13, 35)

        tag_6a = [item for item in tax_tag_name if ('+6(a)' in item or '-6(a)' in item) and 'Tax' in item]
        if tag_6a:
            aml_6a_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_6a)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 13,
                              'Purchases (except import of goods) - BOX 6(a)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Company Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Invoice # / Document #', style_specification_data_brown)
            sheet.write(row, col + 4, 'Invoice/ Document Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Invoice Amount OMR (before VAT)',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'VAT Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 8, 'Supplier Name', style_specification_data_brown)
            sheet.write(row, col + 9, 'Supplier Country', style_specification_data_brown)
            sheet.write(row, col + 10, 'Amount paid to Directorate General for Customs Box 4(b)',
                        style_specification_data_brown)
            sheet.write(row, col + 11, 'Customs Declaration Number', style_specification_data_brown)
            sheet.write(row, col + 12, 'Clear description of the goods imported', style_specification_data_brown)
            sheet.write(row, col + 13, 'Deductible VAT OMR Box 6(b)', style_specification_data_brown)

            row = row + 1
            col = col
            serial_a6 = 1
            total_a6_base_amount = 0.00
            total_a6_balance = 0.00

            if aml_6a_ids:
                for a6 in aml_6a_ids:
                    sheet.write(row, col, serial_a6, style_specification_data_white_center)
                    sheet.write(row, col + 1, a6.company_id.vat if a6.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, a6.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, a6.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, a6.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, "{: .2f}".format(a6.tax_base_amount) + ' ' + str(a6.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 7,
                                "{: .2f}".format(abs(a6.balance)) + ' ' + str(a6.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 8, a6.partner_id.name, style_specification_data_white_left)
                    sheet.write(row, col + 9, a6.partner_id.country_id.name if a6.partner_id.country_id.name else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 10, ' ',
                                style_specification_data_white_left)
                    sheet.write(row, col + 11, ' ', style_specification_data_white_left)
                    sheet.write(row, col + 12, a6.name,
                                style_specification_data_white_left)
                    sheet.write(row, col + 13, ' ', style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_a6 += 1
                    total_a6_base_amount += a6.tax_base_amount
                    total_a6_balance += abs(a6.balance)

            row = row
            col = col

            sheet.write(row, col + 5, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 6,
                        "{: .2f}".format(total_a6_base_amount) + ' ' + str(self.company_id.currency_id.name),
                        style_specification_data_white_right)
            sheet.write(row, col + 7,
                        "{: .2f}".format(total_a6_balance) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 13,
                              'Total value of all imports, including exempt/zero rated goods and those where import VAT has been paid to the Directorate General of Customs.  Excludes imports reported in Box 4a.',
                              style_specification_data_white_left)

        ###############################################################################################

        sheet = workbook.add_worksheet('Import - Box 6(b)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 40)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 30)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)
        sheet.set_column(11, 11, 35)
        sheet.set_column(12, 12, 35)
        sheet.set_column(13, 13, 35)

        tag_6b = [item for item in tax_tag_name if ('+6(b)' in item or '-6(b)' in item) and 'Tax' in item]
        if tag_6b:
            aml_6b_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_6b)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 13,
                              'Import of goods - Box 6(b)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Company Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Invoice # / Document #', style_specification_data_brown)
            sheet.write(row, col + 4, 'Invoice/ Document Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Invoice Amount OMR (before VAT)',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'VAT Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 8, 'Supplier Name', style_specification_data_brown)
            sheet.write(row, col + 9, 'Supplier Country', style_specification_data_brown)
            sheet.write(row, col + 10, 'Taxable amount to be reported on VAT return',
                        style_specification_data_brown)
            sheet.write(row, col + 11, 'Customs Declaration Number', style_specification_data_brown)
            sheet.write(row, col + 12, 'Clear description of the goods imported', style_specification_data_brown)
            sheet.write(row, col + 13, 'Deductible VAT OMR Box 6(b)', style_specification_data_brown)

            row = row + 1
            col = col
            serial_b6 = 1
            total_b6_base_amount = 0.00
            total_b6_balance = 0.00

            if aml_6b_ids:
                for b6 in aml_6b_ids:
                    sheet.write(row, col, serial_b6, style_specification_data_white_center)
                    sheet.write(row, col + 1, b6.company_id.vat if b6.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, b6.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, b6.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, b6.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, "{: .2f}".format(b6.tax_base_amount) + ' ' + str(b6.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 7,
                                "{: .2f}".format(abs(b6.balance)) + ' ' + str(b6.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 8, b6.partner_id.name, style_specification_data_white_left)
                    sheet.write(row, col + 9, b6.partner_id.country_id.name if b6.partner_id.country_id.name else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 10, '',
                                style_specification_data_white_left)
                    sheet.write(row, col + 11, '', style_specification_data_white_left)
                    sheet.write(row, col + 12, b6.name,
                                style_specification_data_white_left)
                    sheet.write(row, col + 13, '', style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_b6 += 1
                    total_b6_base_amount += b6.tax_base_amount
                    total_b6_balance += abs(b6.balance)

            row = row
            col = col

            sheet.write(row, col + 5, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 6,
                        "{: .2f}".format(total_b6_base_amount) + ' ' + str(self.company_id.currency_id.name),
                        style_specification_data_white_right)
            sheet.write(row, col + 7,
                        "{: .2f}".format(total_b6_balance) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 13,
                              'Total value (excluding VAT) of standard rated imports of goods whether or not postponed.',
                              style_specification_data_white_left)

        ##############################################################################################

        sheet = workbook.add_worksheet('Fixed Assets - Box 6(c)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 50)
        sheet.set_column(7, 7, 40)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 40)
        sheet.set_column(11, 11, 35)
        sheet.set_column(12, 12, 35)

        tag_6c = [item for item in tax_tag_name if ('+6(c)' in item or '-6(c)' in item) and 'Tax' in item]
        if tag_6c:
            aml_6c_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_6c)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 12,
                              'VAT on acquisition of fixed assets - Box 6(c)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col
            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Tax Invoice/Tax Credit Note #', style_specification_data_brown)
            sheet.write(row, col + 4, 'Tax Invoice/Tax Credit Note Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Tax Invoice/Tax credit note Received Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'Tax Invoice/Tax credit note Amount OMR (before VAT)',
                        style_specification_data_brown)
            sheet.write(row, col + 8, 'VAT Amount OMR', style_specification_data_brown)
            sheet.write(row, col + 9, 'VAT Amount Claimed OMR', style_specification_data_brown)
            sheet.write(row, col + 10, 'Supplier Name',
                        style_specification_data_brown)
            sheet.write(row, col + 11, 'Supplier VATIN', style_specification_data_brown)
            sheet.write(row, col + 12, 'Clear description of the supply', style_specification_data_brown)

            row = row + 1
            col = col
            serial_c6 = 1

            total_c6_base_amount = 0.00
            total_c6_balance = 0.00

            if aml_6c_ids:
                for c6 in aml_6c_ids:
                    sheet.write(row, col, serial_c6, style_specification_data_white_center)
                    sheet.write(row, col + 1, c6.company_id.vat if c6.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, c6.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, c6.move_id.name, style_specification_data_white_center)
                    sheet.write(row, col + 4, c6.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, c6.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 7, "{: .2f}".format(c6.tax_base_amount) + ' ' + str(c6.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 8,
                                "{: .2f}".format(abs(c6.balance)) + ' ' + str(c6.currency_id.name),
                                style_specification_data_white_right)
                    sheet.write(row, col + 9, ' ', style_specification_data_white_left)
                    sheet.write(row, col + 10, c6.partner_id.name,
                                style_specification_data_white_left)
                    sheet.write(row, col + 11, c6.partner_id.vat if c6.partner_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 12, c6.name, style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_c6 += 1
                    total_c6_base_amount += c6.tax_base_amount
                    total_c6_balance += abs(c6.balance)

            row = row
            col = col

            sheet.write(row, col + 6, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 7,
                        "{: .2f}".format(total_c6_base_amount) + ' ' + str(self.company_id.currency_id.name),
                        style_specification_data_white_right)
            sheet.write(row, col + 8,
                        "{: .2f}".format(total_c6_balance) + ' ' + str(
                            self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 12,
                              'Purchase, acquisition or construction of capital assets. ',
                              style_specification_data_white_left)

        #######################################################################################

        sheet = workbook.add_worksheet('Input Adjustments - Box 6(d)')

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 40)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 45)
        sheet.set_column(5, 5, 50)
        sheet.set_column(6, 6, 50)
        sheet.set_column(7, 7, 40)

        tag_6d = [item for item in tax_tag_name if ('+6(d)' in item or '-6(d)' in item) and 'Tax' in item]
        if tag_6d:
            aml_6d_ids = self.env['account.move.line'].search([
                ('date', '>=', self.start_date),
                ('date', '<=', self.end_date),
                ('parent_state', '=', 'posted'),
                ('company_id', '=', self.company_id.id),
                ('tax_tag_ids.name', 'in', tag_6d)
            ])

            row = 0
            col = 0
            sheet.merge_range(row, col, row, col + 7,
                              'Adjustment of input VAT credit - Box 6(d)* - If Group Should be Split By Group Member',
                              style_specification_data_white_left)

            row = row + 1
            col = col

            sheet.write(row, col, 'Serial #', style_specification_data_brown)
            sheet.write(row, col + 1, 'Taxpayer VATIN', style_specification_data_brown)
            sheet.write(row, col + 2, 'Taxpayer Name / Member Company Name (If applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 3, 'Tax Invoice/Tax Credit Note # (if applicable)',
                        style_specification_data_brown)
            sheet.write(row, col + 4, 'Transaction / Adjustment Date - DD/MM/YYYY format only',
                        style_specification_data_brown)
            sheet.write(row, col + 5, 'Reporting period (From DD/MM/YYYY to DD/MM/YYYY format only)',
                        style_specification_data_brown)
            sheet.write(row, col + 6, 'VAT Amount Claimed OMR',
                        style_specification_data_brown)
            sheet.write(row, col + 7, 'Clear description of the adjustment',
                        style_specification_data_brown)

            row = row + 1
            col = col
            serial_d6 = 1
            total_d6_vat_claim = 0.00

            if aml_6d_ids:
                for d6 in aml_6d_ids:
                    sheet.write(row, col, serial_d6, style_specification_data_white_center)
                    sheet.write(row, col + 1, d6.company_id.vat if d6.company_id.vat != 0 else '',
                                style_specification_data_white_center)
                    sheet.write(row, col + 2, d6.company_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 3, d6.move_id.name,
                                style_specification_data_white_center)
                    sheet.write(row, col + 4, d6.date.strftime("%d/%m/%Y"),
                                style_specification_data_white_center)
                    sheet.write(row, col + 5, str(start_date) + ' to ' + str(end_date),
                                style_specification_data_white_center)
                    sheet.write(row, col + 6, "{: .2f}".format(abs(d6.balance)) + ' ' + str(d6.currency_id.name),
                                style_specification_data_white_left)
                    sheet.write(row, col + 7, d6.name,
                                style_specification_data_white_left)

                    row = row + 1
                    col = col
                    serial_d6 += 1
                    total_d6_vat_claim += abs(d6.balance)

            row = row
            col = col

            sheet.write(row, col + 5, 'Total',
                        style_specification_data_white_right)
            sheet.write(row, col + 6,
                        "{: .2f}".format(total_d6_vat_claim) + ' ' + str(self.company_id.currency_id.name),
                        style_specification_data_white_right)

            row = row + 1
            col = col
            sheet.merge_range(row, col, row, col + 7,
                              'Any adjustments to VAT deductible that must be declared in this period including bad debts related to standard rated supplies, refunds, returns, and any other adjustments affecting VAT deductible.',
                              style_specification_data_white_left)

        ###################################################################################
