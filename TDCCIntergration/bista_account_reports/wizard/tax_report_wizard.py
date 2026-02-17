# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
import warnings

import base64
import io

from odoo.exceptions import UserError

try:
    import xlwt
except ImportError:
    xlwt = None


class TaxReportWizard(models.TransientModel):
    _name = 'tax.report.wizard'
    _description = 'Account Report'

    start_date = fields.Date(string='Start Date',
                             default=fields.date.today())
    end_date = fields.Date(string='End Date',
                           default=fields.date.today())

    def get_data(self):
        start_date = self.start_date
        end_date = self.end_date
        utz = self.env.user.tz or 'UTC'

        where1 = """and vendor.vat <> '' and vendor.supplier_rank > 0"""
        where2 = """and vendor.vat IS NULL and vendor.supplier_rank > 0"""
        where3 = """and vendor.customer_rank > 0"""

        query = """ select
                                        aa.name as accountname,
                                        TO_CHAR(am.invoice_date :: DATE, 'dd/mm/yyyy') as invoicedate,
                                        am.name as vno,
                                        am.ref as invno,
                                        vendor.name as mainaccountname,
                                        aa.code as acccode,
                                        aa.name as accaame,
                                        vendor.vat as trnno,
                                        am.vat_description as description,
                                        ait.debit as debit,
                                        0.0 as credit,
                                        ait.price_total - ait.price_subtotal AS taxamount
                                    from account_move_line ait
                                        join account_move am
                                        on ait.move_id = am.id
                                        join res_partner vendor
                                        on am.partner_id = vendor.id
                                        join account_account aa on
                                        ait.account_id = aa.id
                                    where am.state not in ('draft','cancel') and 
                                    am.invoice_date >= '%s' and
                                    am.invoice_date <= '%s' """ % (start_date, end_date)

        aml_query = """select
                                          tax.name as accountname,
                                          TO_CHAR(aml.date_maturity :: DATE, 'dd/mm/yyyy') as invoicedate,
                                          am.name as vno,
                                          am.ref as invno,
                                          vendor.name as mainaccountname,
                                          aa.code as acccode,
                                          aa.name as accaame,
                                          vendor.vat as trnno,
                                          aml.name as description,
                                          (select sum(aml2.debit)
                                              from account_move_line_account_tax_rel amlt
                                              left join account_move_line aml2
                                              on amlt.account_move_line_id=aml2.id
                                              where aml2.move_id=am.id and
                                              amlt.account_tax_id=tax.id) as debit,
                                          0.0 as credit,
                                          aml.debit as taxamount
                                  from account_move_line aml
                                          join res_partner vendor
                                          on aml.partner_id = vendor.id
                                          join account_move am
                                          on aml.move_id = am.id
                                          join account_account aa on
                                          aml.account_id = aa.id
                                          join account_tax tax on
                                          aml.tax_line_id = tax.id
                                  where aml.tax_line_id is not null and
                                          aml.move_id is null and
                                          am.date >= '%s' and
                                          am.date <= '%s' and
                                          am.state = 'posted' """ % (start_date, end_date)

        # Fetch data from database
        with_trn_qry = query + where1
        self._cr.execute(with_trn_qry)
        trn_res = self._cr.dictfetchall()

        without_trn_qry = query + where2
        self._cr.execute(without_trn_qry)
        without_trn_res = self._cr.dictfetchall()

        customer_qry = query + where3
        self._cr.execute(customer_qry)
        customer_res = self._cr.dictfetchall()

        # Fetch Journal Items with and without TRN number
        with_trn_aml = aml_query + where1
        self._cr.execute(with_trn_aml)
        trn_aml_res = self._cr.dictfetchall()
        trn_res += trn_aml_res

        without_trn_aml = aml_query + where2
        self._cr.execute(without_trn_aml)
        without_trn_aml_res = self._cr.dictfetchall()
        without_trn_res += without_trn_aml_res

        # Fetch Journal Items with no partner
        no_partner_aml = """select
                                        tax.name as accountname,
                                        TO_CHAR(aml.date_maturity :: DATE, 'dd/mm/yyyy') as invoicedate,
                                        am.name as vno,
                                        am.ref as invno,
                                        '' as mainaccountname,
                                        aa.code as acccode,
                                        aa.name as accaame,
                                        '' as trnno,
                                        aml.name as description,
                                        (select sum(aml2.debit)
                                        from account_move_line_account_tax_rel amlt
                                        left join account_move_line aml2
                                        on amlt.account_move_line_id=aml2.id
                                        where aml2.move_id=am.id and
                                        amlt.account_tax_id=tax.id) as debit,
                                        0.0 as credit,
                                        aml.debit as taxamount
                                from account_move_line aml
                                        join account_move am
                                        on aml.move_id = am.id
                                        join account_account aa on
                                        aml.account_id = aa.id
                                        join account_tax tax on
                                        aml.tax_line_id = tax.id
                                where aml.tax_line_id is not null and
                                        aml.move_id is null and
                                        am.date >= '%s' and
                                        am.date <= '%s' and
                                        am.state = 'posted' and
                                        aml.partner_id is NULL""" % (start_date, end_date)
        self._cr.execute(no_partner_aml)
        no_partner_aml_res = self._cr.dictfetchall()
        without_trn_res += no_partner_aml_res

        if not (trn_res or without_trn_res or customer_res):
            raise UserError(_("There is no data with selected options."))
        else:
            # Safely set debit and taxamount to 0.0 if None
            for record in trn_res + without_trn_res + customer_res:
                record['debit'] = record.get('debit') if record.get('debit') is not None else 0.0
                record['taxamount'] = record.get('taxamount') if record.get('taxamount') is not None else 0.0

            return trn_res, without_trn_res, customer_res

    # @api.multi
    def print_pdf_report(self):
        self.ensure_one()
        [data] = self.read()

        trn_res, without_trn_res, customer_res = self.get_data()

        # Filter out zero-value lines
        def filter_zero_lines(data):
            return [
                rec for rec in data
                if (rec.get('debit') or 0.0) != 0.0 or (rec.get('taxamount') or 0.0) != 0.0
            ]

        form_data = [
            filter_zero_lines(trn_res),
            filter_zero_lines(without_trn_res),
            filter_zero_lines(customer_res),
        ]

        datas = {
            'ids': self._ids,
            'model': 'account.invoice.tax',
            'form': data,
            'form_data': form_data
        }

        return self.env.ref(
            'bista_account_reports.action_vat_report'
        ).report_action(self, data=datas)
    # @api.multi

    def print_xls_report(self):
        def write_header(ws, row):
            headers = ['VNo', 'Inv No', 'Date', 'AccountName', 'TRN No', 'Description', 'Vat Amount', 'TaxAmt',
                       'TotalAmt']
            for i, header in enumerate(headers):
                ws.write(row, i, header, style)

        def write_section_title(ws, row, title):
            ws.write(row, 0, title, style)
            return row + 1

        def write_data_rows(ws, start_row, records):
            total_debit = total_tax = 0.0
            row = start_row
            for rec in records:
                debit = rec.get('debit') or 0.0
                taxamount = rec.get('taxamount') or 0.0

                if debit == 0.0 and taxamount == 0.0:
                    continue  # Skip this record

                col = 0
                total = debit + taxamount
                fields = [
                    rec.get('vno'), rec.get('invno'), rec.get('invoicedate'), rec.get('mainaccountname'),
                    rec.get('trnno'), rec.get('description'), debit, taxamount, total
                ]
                for value in fields:
                    ws.write(row, col, value, data_style)
                    col += 1
                total_debit += debit
                total_tax += taxamount
                row += 1
            return row, total_debit, total_tax

        def write_totals(ws, row, debit_total, tax_total):
            ws.write(row, 5, 'Net Total', style)
            ws.write(row, 6, debit_total, style)
            ws.write(row, 7, tax_total, style)
            ws.write(row, 8, debit_total + tax_total, style)

        # Setup workbook and styles
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Vat Report', cell_overwrite_ok=True)

        pattern = xlwt.Pattern()
        pattern.pattern = xlwt.Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = xlwt.Style.colour_map['pale_blue']
        style = xlwt.easyxf("font: bold on; alignment: horiz centre;")
        style.pattern = pattern
        data_style = xlwt.easyxf("alignment: horiz centre;")

        for i in range(11):
            worksheet.col(i).width = 18 * 256

        row = 0
        write_header(worksheet, row)
        row += 2

        trn_data, without_trn_data, customer_data = self.get_data()

        # Input VAT Section
        row = write_section_title(worksheet, row, 'Input Vat')
        row, debit_total, tax_total = write_data_rows(worksheet, row, trn_data)
        write_totals(worksheet, row, debit_total, tax_total)
        row += 3

        # Output VAT Section
        row = write_section_title(worksheet, row, 'Output Vat')
        row, debit_total, tax_total = write_data_rows(worksheet, row, customer_data)
        write_totals(worksheet, row, debit_total, tax_total)
        row += 3

        # VAT Non-Refundable Expense Section
        row = write_section_title(worksheet, row, 'VAT Non-Refundable Expense')
        row, debit_total, tax_total = write_data_rows(worksheet, row, without_trn_data)
        write_totals(worksheet, row, debit_total, tax_total)

        # Save and return report
        stream = io.BytesIO()
        workbook.save(stream)
        vals = {
            'tax_xls_output': base64.encodebytes(stream.getvalue()),
            'name': 'VAT Report.xls'
        }
        attach_id = self.env['tax.report.print.link'].create(vals)

        return {
            'context': self.env.context,
            'name': 'Vat Report',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tax.report.print.link',
            'type': 'ir.actions.act_window',
            'res_id': attach_id.id,
            'target': 'new'
        }

class TaxReportPrintLink(models.TransientModel):
    _name = 'tax.report.print.link'
    _description = 'TaxReport Link'

    tax_xls_output = fields.Binary(string='Excel Output')
    name = fields.Char(
        string='File Name',
        help='Save report as .xls format')
