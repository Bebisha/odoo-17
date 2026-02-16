from base64 import encodebytes
from io import BytesIO
import xlsxwriter
from odoo.exceptions import ValidationError
from odoo import models, fields, _
from datetime import datetime


class KGStockExcelReportWizard(models.TransientModel):
    _name = "stock.excel.report.wizard"
    _description = "Stock Report - Excel"

    name = fields.Char(string="Reference")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    def print_excel_report(self):
        if self.start_date > self.end_date:
            raise ValidationError(_('Start Date must be less than End Date'))

        domain = [('date', '>=', self.start_date), ('date', '<=', self.end_date), ('state', '=', 'done'),
                  ('company_id', '=', self.company_id.id)]

        move_ids = self.env['stock.move'].search(domain, order='date asc')

        if not move_ids:
            raise ValidationError(_('No data in this date range'))

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

        report_name = 'Stock Summary'
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }

    def generate_xlsx_report(self, workbook, data=None, objs=None):
        sheet = workbook.add_worksheet('Stock Summary')

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
        style_specification_data_white_right.set_text_wrap()
        style_specification_data_white_right.set_align('right')
        style_specification_data_white_right.set_border()

        style_specification_data_white_left = workbook.add_format()
        style_specification_data_white_left.set_fg_color('white')
        style_specification_data_white_left.set_font_name('Times New Roman')
        style_specification_data_white_left.set_text_wrap()
        style_specification_data_white_left.set_align('left')
        style_specification_data_white_left.set_border()

        style_specification_data_white_right_bold = workbook.add_format()
        style_specification_data_white_right_bold.set_fg_color('white')
        style_specification_data_white_right_bold.set_font_name('Times New Roman')
        style_specification_data_white_right_bold.set_text_wrap()
        style_specification_data_white_right_bold.set_align('right')
        style_specification_data_white_right_bold.set_border()
        style_specification_data_white_right_bold.set_bold()

        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 50)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 15)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 15)
        sheet.set_column(11, 11, 15)
        sheet.set_column(12, 12, 15)
        sheet.set_column(13, 13, 15)

        row = 0
        col = 0
        sheet.write(row, col + 1, str(self.company_id.name), style_specification_data_white_center)

        row = row + 1
        col = col
        sheet.write(row, col + 1, str(self.company_id.country_id.name), style_specification_data_white_center)

        row = row + 1
        col = col
        sheet.write(row, col + 1, 'STOCK SUMMARY', style_specification_data_white_center)

        start_date = self.start_date.strftime("%d-%m-%Y")
        end_date = self.end_date.strftime("%d-%m-%Y")

        row = row + 1
        col = col
        sheet.merge_range(row, col + 2, row, col + 13,
                          str(self.company_id.name) + '-Inventory From ' + str(start_date) + ' To ' + str(end_date),
                          style_specification_data_white_center)

        row = row + 1
        col = col
        sheet.merge_range(row, col + 2, row, col + 4, 'Opening Balance', style_specification_data_white_center)
        sheet.merge_range(row, col + 5, row, col + 7, 'Inwards', style_specification_data_white_center)
        sheet.merge_range(row, col + 8, row, col + 10, 'Outwards', style_specification_data_white_center)
        sheet.merge_range(row, col + 11, row, col + 13, 'Closing Balance', style_specification_data_white_center)

        row = row + 1
        col = col
        # sheet.merge_range(row, col + 1, row + 1, col + 1, 'Particulars', style_specification_data_white_center)
        sheet.write(row, col + 1, 'Particulars', style_specification_data_white_center)
        sheet.write(row, col + 2, 'Quantity', style_specification_data_white_center)
        sheet.write(row, col + 3, 'Rate', style_specification_data_white_center)
        sheet.write(row, col + 4, 'Value', style_specification_data_white_center)
        sheet.write(row, col + 5, 'Quantity', style_specification_data_white_center)
        sheet.write(row, col + 6, 'Rate', style_specification_data_white_center)
        sheet.write(row, col + 7, 'Value', style_specification_data_white_center)
        sheet.write(row, col + 8, 'Quantity', style_specification_data_white_center)
        sheet.write(row, col + 9, 'Rate', style_specification_data_white_center)
        sheet.write(row, col + 10, 'Value', style_specification_data_white_center)
        sheet.write(row, col + 11, 'Quantity', style_specification_data_white_center)
        sheet.write(row, col + 12, 'Rate', style_specification_data_white_center)
        sheet.write(row, col + 13, 'Value', style_specification_data_white_center)

        domain = [('date', '>=', self.start_date), ('date', '<=', self.end_date), ('state', '=', 'done'),
                  ('company_id', '=', self.company_id.id)]

        move_ids = self.env['stock.move'].search(domain, order='date asc')
        if move_ids:
            total_opening_value = 0
            total_inwards_value = 0
            total_outwards_value = 0
            total_closing_value = 0
            for product in move_ids.mapped('product_id'):
                if product.detailed_type == 'product':
                    ledger_moves = move_ids.filtered(lambda x: x.product_id == product)

                    in_qty_moves = ledger_moves.filtered(
                        lambda x: x.location_usage not in ('internal', 'transit') and x.location_dest_usage in (
                            'internal', 'transit'))
                    in_qty = sum(in_qty_moves.mapped('quantity'))

                    out_qty_moves = ledger_moves.filtered(
                        lambda x: x.location_usage in ('internal', 'transit') and x.location_dest_usage not in (
                            'internal', 'transit'))
                    out_qty = sum(out_qty_moves.mapped('quantity'))

                    opening_qty = product.with_context(to_date=self.start_date).qty_available
                    opening_cost = product.with_context(to_date=self.start_date).standard_price

                    product_cost = product.with_context(to_date=self.end_date).standard_price

                    closing_qty = opening_qty
                    closing_qty += in_qty - out_qty

                    format_opening_qty = "{: .2f}".format(opening_qty)
                    format_in_qty = "{: .2f}".format(in_qty)
                    format_out_qty = "{: .2f}".format(out_qty)
                    format_closing_qty = "{: .2f}".format(closing_qty)

                    opening_qty_uom = f"{format_opening_qty} {product.uom_id.name}" if opening_qty != 0.00 else ''
                    opening_cost = opening_cost
                    format_opening_cost = "{: .2f}".format(opening_cost) if opening_qty != 0.00 else ''
                    opening_value = opening_qty * opening_cost
                    format_opening_value = "{: .2f}".format(opening_value) if opening_qty != 0.00 else ''

                    inwards_qty_uom = f"{format_in_qty} {product.uom_id.name}" if in_qty != 0.00 else ''
                    inwards_cost = product_cost
                    format_inwards_cost = "{: .2f}".format(inwards_cost) if in_qty != 0.00 else ''
                    inwards_value = in_qty * product_cost
                    format_inwards_value = "{: .2f}".format(inwards_value) if in_qty != 0.00 else ''

                    outwards_qty_uom = f"{format_out_qty} {product.uom_id.name}" if out_qty != 0.00 else ''
                    outwards_cost = product_cost
                    format_outwards_cost = "{: .2f}".format(outwards_cost) if out_qty != 0.00 else ''
                    outwards_value = out_qty * product_cost
                    format_outwards_value = "{: .2f}".format(outwards_value) if out_qty != 0.00 else ''

                    closing_qty_uom = f"{format_closing_qty} {product.uom_id.name}" if closing_qty != 0.00 else ''
                    closing_cost = product_cost
                    format_closing_cost = "{: .2f}".format(closing_cost) if closing_qty != 0.00 else ''
                    closing_value = closing_qty * closing_cost
                    format_closing_value = "{: .2f}".format(closing_value) if closing_qty != 0.00 else ''

                    row = row + 1
                    col = col
                    sheet.write(row, col + 1, product.display_name, style_specification_data_white_left)

                    sheet.write(row, col + 2, opening_qty_uom, style_specification_data_white_right)
                    sheet.write(row, col + 3, format_opening_cost, style_specification_data_white_right)
                    sheet.write(row, col + 4, format_opening_value, style_specification_data_white_right)

                    sheet.write(row, col + 5, inwards_qty_uom, style_specification_data_white_right)
                    sheet.write(row, col + 6, format_inwards_cost, style_specification_data_white_right)
                    sheet.write(row, col + 7, format_inwards_value, style_specification_data_white_right)

                    sheet.write(row, col + 8, outwards_qty_uom, style_specification_data_white_right)
                    sheet.write(row, col + 9, format_outwards_cost, style_specification_data_white_right)
                    sheet.write(row, col + 10, format_outwards_value, style_specification_data_white_right)

                    sheet.write(row, col + 11, closing_qty_uom, style_specification_data_white_right)
                    sheet.write(row, col + 12, format_closing_cost, style_specification_data_white_right)
                    sheet.write(row, col + 13, format_closing_value, style_specification_data_white_right)

                    total_opening_value += opening_value
                    total_inwards_value += inwards_value
                    total_outwards_value += outwards_value
                    total_closing_value += closing_value

            format_total_opening_value = "{: .2f}".format(total_opening_value)
            format_total_inwards_value = "{: .2f}".format(total_inwards_value)
            format_total_outwards_value = "{: .2f}".format(total_outwards_value)
            format_total_closing_value = "{: .2f}".format(total_closing_value)

            row = row + 1
            col = col
            sheet.write(row, col + 1, 'Grand Total', style_specification_data_white_center)
            sheet.merge_range(row, col + 2, row, col + 4, format_total_opening_value,
                              style_specification_data_white_right_bold)
            sheet.merge_range(row, col + 5, row, col + 7, format_total_inwards_value,
                              style_specification_data_white_right_bold)
            sheet.merge_range(row, col + 8, row, col + 10, format_total_outwards_value,
                              style_specification_data_white_right_bold)
            sheet.merge_range(row, col + 11, row, col + 13, format_total_closing_value,
                              style_specification_data_white_right_bold)
