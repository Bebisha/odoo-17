# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

import io
import base64
try:
    import xlwt
except ImportError:
    xlwt = None


class SaleCommissionWizard(models.TransientModel):
    _name = 'wizard.sale.commission'
    _description = 'Commission XLS Report'

    partner_ids = fields.Many2many('res.partner')
    to_date = fields.Date(string="As of")

    def action_unposted_lines(self):
        user_ids = self.env['account.move'].search([
            ('state', 'not in', ('draft', 'cancel'))]).mapped('user_id')
        today_date = date.today()
        commission_obj = self.env['sale.commission']
        commission_line_obj = self.env['sale.commission.line']
        action = self.env.ref(
            'bista_tdcc_commission.action_show_unposted_comm_line_tree'
        ).read()[0]
        for user in user_ids:
            if not user.partner_id.cut_off_date:
                raise UserError(_(
                    "Please configure cut off date on salesperson %s"
                    % user.partner_id.name))
            cutoff_month = today_date.strftime('%m')
            cutoff_date = user.partner_id.cut_off_date.strftime('%d')

            cut_off_date = today_date.replace(
                month=int(cutoff_month), day=int(cutoff_date))
            if cut_off_date > today_date:
                cut_off_date = cut_off_date + relativedelta(months=-1)

            commission_ids = commission_obj.search([
                ('end_date', '<=', str(cut_off_date))])

            commission_line_obj |= commission_line_obj.search([
                ('commission_date', '<', str(cut_off_date)),
                ('state', '=', 'unpaid'),
                ('commission_amount', '>', 0.00),
                ('commission_id', 'in', commission_ids.ids)])
        action['domain'] = [('id', 'in', commission_line_obj.ids)]
        return action

    def get_row_title(self):
        headers = ['sales', 'receipt', 'balance', 'commission_sales',
                   'commission_receipt']
        header_title = {'sales': _("Sales"),
                        'receipt': _("RECEIPT"),
                        'balance': _("BALANCE"),
                        'commission_sales': _("Commision by Sales"),
                        'commission_receipt': _("Commision by Receipt")
                        }
        return headers, header_title

    def get_column_title(self):
        months_header = []
        months_header_title = {}
        wizard_year = self.to_date.strftime('%Y')
        for i in range(1, 13):
            months_header.append(date(int(wizard_year), i, 1).strftime('%b'))
            months_header_title[date(
                int(wizard_year), i, 1).strftime(
                    '%b')] = date(int(wizard_year), i, 1).strftime('%B')
        return months_header, months_header_title

    def set_rows(self, workbook, worksheet, row_headers, row_header_title):
        column_counter = 1
        style = xlwt.easyxf("font: bold on; alignment: horiz centre;")
        for header in row_headers:
            worksheet.col(column_counter).width = 256 * 20
            worksheet.write(3, column_counter, row_header_title.get(header),
                            style)
            column_counter += 1
        return column_counter

    def set_column(self, workbook, worksheet,
                   months_header, months_header_title):
        row_counter = 4
        style = xlwt.easyxf("font: bold on; alignment: horiz centre;")
        worksheet.write(3, 0, 'Months', style)
        for header in months_header:
            #             worksheet.row(row_counter).height = 256 * 10
            worksheet.write(row_counter, 0, months_header_title.get(header),
                            style)
            row_counter += 1
        return row_counter

    def write_line_data(self, worksheet, row, commission_id):
        receipt_commission_id = self.env['receipt.commission'].search([
            ('partner_id', '=', commission_id.partner_id.id),
            ('start_date', '=', commission_id.start_date),
            ('end_date', '=', commission_id.end_date)], limit=1)
        col = 1
        worksheet.write(row, col, commission_id.sales_amount or 0.00)
        col += 1
        worksheet.write(row, col, commission_id.receipt_amount or 0.00)
        col += 1
        balance = commission_id.sales_amount - commission_id.receipt_amount
        worksheet.write(row, col, balance or 0.00)
        col += 1
        worksheet.write(row, col, commission_id.commission_by_sales or 0.00)
        col += 1
        worksheet.write(row, col, receipt_commission_id.amount or 0.00)
        col += 1
        return worksheet

    # @api.multi
    def action_print_report(self):
        workbook = xlwt.Workbook()
        wizard_year = self.to_date.strftime('%Y')
        partner_ids = self.partner_ids
        commission_obj = self.env['sale.commission']
        if not partner_ids:
            partner_ids = self.env['res.partner'].search([]).ids
            partner_ids = commission_obj.search([
                ('partner_id', 'in', partner_ids)]).mapped('partner_id')
        wizard_month = int(self.to_date.strftime('%m'))
        row_headers, row_header_title = self.get_row_title()
        months_header, months_header_title = self.get_column_title()
        style = xlwt.easyxf("font: bold on; alignment: horiz centre;")
        commission_obj = self.env['sale.commission']
        row_counter = 0
        for partner in partner_ids:
            worksheet = workbook.add_sheet(partner.name + '-' + wizard_year,
                                           cell_overwrite_ok=True)
            worksheet.col(0).width = 256 * 20
            worksheet.col(1).width = 256 * 20
            worksheet.write(0, 1, partner.name, style)
            worksheet.write(0, 2, 'As of ' + self.to_date.strftime('%b %d %Y'),
                            style)
            worksheet.write(1, 1, 'Commission ' + wizard_year, style)
            self.set_rows(workbook, worksheet, row_headers, row_header_title)
            row_counter = self.set_column(workbook, worksheet, months_header,
                                          months_header_title)
            row = 4
            total_sales = total_receipt = total_balance = 0.00
            total_commission_by_sales = total_commission_by_receipt = 0.00
            for month in range(1, wizard_month + 1):
                from_date = self.to_date.replace(month=month, day=1)
                to_date = from_date + relativedelta(day=31)
                domain = [('partner_id', '=', partner.id),
                          ('start_date', '>=', str(from_date)),
                          ('end_date', '<=', str(to_date))]
                commission_id = commission_obj.search(domain)
                self.write_line_data(worksheet, row, commission_id)
                total_sales += commission_id.sales_amount
                total_receipt += commission_id.receipt_amount
                total_balance += commission_id.sales_amount - \
                    commission_id.receipt_amount
                total_commission_by_sales += commission_id.commission_by_sales
                total_commission_by_receipt += \
                    commission_id.commission_by_receipt
                row += 1

            worksheet.write(row_counter, 1, total_sales, style)
            worksheet.write(row_counter, 2, total_receipt, style)
            worksheet.write(row_counter, 3, total_balance, style)
            worksheet.write(row_counter, 4, total_commission_by_sales, style)
            worksheet.write(row_counter, 5, total_commission_by_receipt, style)

        stream = io.BytesIO()
        workbook.save(stream)
        attach_id = self.env['commission.report.print.link'].sudo().create({
            'name': 'Commission Report.xls',
            'commission_xls_output': base64.b64encode(stream.getvalue())
        })

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'commission.report.print.link',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class CommissionReportPrintLink(models.Model):
    _name = 'commission.report.print.link'
    _description = 'Commission Report Link'

    commission_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format')
