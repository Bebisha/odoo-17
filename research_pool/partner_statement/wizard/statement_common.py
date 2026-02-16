# Copyright 2018 Graeme Gellatly
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from base64 import encodebytes
from datetime import datetime, timedelta
from io import BytesIO

import xlsxwriter
from dateutil.relativedelta import relativedelta
import io

from odoo import api, fields, models


class StatementCommon(models.AbstractModel):
    _name = "statement.common.wizard"
    _description = "Statement Reports Common Wizard"

    def get_default_partner_ids(self):
        if self._context.get('active_ids'):
            return len(self._context['active_ids'])
        else:
            return len(self.env['res.partner'].search([]).ids)

    name = fields.Char()
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        string="Company",
        required=True,
    )
    partner_id = fields.Many2one('res.partner', 'Partner' ,required=True)
    date_end = fields.Date(required=True, default=fields.Date.context_today)
    show_aging_buckets = fields.Boolean(string="Show Aging Bucket",default=True)
    number_partner_ids = fields.Integer(
        default=get_default_partner_ids
    )
    filter_partners_non_due = fields.Boolean(
        string="Don't show partners with no due entries", default=True
    )
    filter_negative_balances = fields.Boolean("Exclude Negative Balances", default=True)

    aging_type = fields.Selection(
        [("days", "Age by Days"), ("months", "Age by Months")],
        string="Aging Method",
        default="days",
        required=True,
    )

    account_type = fields.Selection(
        [("asset_receivable", "Receivable"), ("liability_payable", "Payable")],
        default="asset_receivable",
    )
    salesperson_wise = fields.Boolean("Salesperson Wise Report", default=False)
    salesperson_id = fields.Many2one('res.users')
    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    @api.onchange("aging_type")
    def onchange_aging_type(self):
        if self.aging_type == "months":
            self.date_end = fields.Date.context_today(self).replace(
                day=1
            ) - relativedelta(days=1)
        else:
            self.date_end = fields.Date.context_today(self)

    def get_default_partner_ids_report(self):
        if self._context.get('active_ids'):
            return self._context['active_ids']
        else:
            if self.partner_id:
                partner = self.env['res.partner'].search([('id', '=', self.partner_id.id)]).ids
            else:
                partner = self.env['res.partner'].search([]).ids
                # print(partner, 'partnerssssssssssssssssssss')
            return partner

    def _prepare_statement(self):
        self.ensure_one()
        return {
            "date_end": self.date_end,
            "company_id": self.company_id.id,
            "partner_ids": self.get_default_partner_ids_report(),
            "show_aging_buckets": self.show_aging_buckets,
            "filter_non_due_partners": self.filter_partners_non_due,
            "account_type": self.account_type,
            "aging_type": self.aging_type,
            "filter_negative_balances": self.filter_negative_balances,
            "salesperson_wise": self.salesperson_wise,
            "salesperson_id": self.salesperson_id.id,
            # 'partner_id':self.partner_id.id
        }

    def button_export_html(self):
        self.ensure_one()
        report_type = "qweb-html"
        return self._export(report_type)

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def button_excel(self):
        # if self.date_from > self.date_to:
        #     raise ValidationError(_('Start Date must be less than End Date'))

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

        report_name = 'outstanding report'
        self.write({'fileout': fout, 'fileout_filename': report_name})
        file_io.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': 'web/content/?model=' + self._name + '&id=' + str(
                self.id) + '&field=fileout&download=true&filename=' + report_name,
        }


    def button_excel(self):
        """print xlsx"""
        active_ids_tmp = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        data = {

            'form': self.read()[0],
            'ids': active_ids_tmp,
            'context': {'active_model': active_model},
        }

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)

        self.generate_xlsx_report(workbook, data=data,date_end=self.date_end,partners=self.partner_id.ids,account_type=self.account_type)

        workbook.close()
        fout = encodebytes(file_io.getvalue())

        datetime_string = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = 'Customer Outstanding Invoice'
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

    def generate_xlsx_report(self, workbook, data,date_end,partners,account_type, objs=None):
        """" for generating xlsx report"""
        sheet = workbook.add_worksheet('General Ledger Report')

        query = """
            SELECT l.id, m.name AS move_id, l.partner_id, l.date, l.name,
                l.blocked, l.currency_id, l.company_id,l.balance,
                CASE WHEN l.ref IS NOT NULL
                    THEN l.ref
                    ELSE m.ref
                END as ref,
                CASE WHEN (l.currency_id is not null AND l.amount_currency > 0.0)
                    THEN avg(l.amount_currency)
                    ELSE avg(l.debit)
                END as debit,
                CASE WHEN (l.currency_id is not null AND l.amount_currency < 0.0)
                    THEN avg(l.amount_currency * (-1))
                    ELSE avg(l.credit)
                END as credit,
                CASE WHEN l.balance > 0.0
                    THEN l.balance - sum(coalesce(pd.amount, 0.0))
                    ELSE l.balance + sum(coalesce(pc.amount, 0.0))
                END AS open_amount,
                CASE WHEN l.balance > 0.0
                    THEN l.amount_currency - sum(coalesce(pd.debit_amount_currency, 0.0))
                    ELSE l.amount_currency + sum(coalesce(pc.credit_amount_currency, 0.0))
                END AS open_amount_currency,
                CASE WHEN l.date_maturity is null
                    THEN l.date
                    ELSE l.date_maturity
                END as date_maturity
            FROM account_move_line l
            JOIN account_account aa ON (aa.id = l.account_id)
            JOIN account_move m ON (l.move_id = m.id)
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.credit_move_id = l2.id
                WHERE l2.date <= %(date_end)s
            ) as pd ON pd.debit_move_id = l.id
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.debit_move_id = l2.id
                WHERE l2.date <= %(date_end)s
            ) as pc ON pc.credit_move_id = l.id
            WHERE l.partner_id IN %(partners)s AND aa.account_type = %(account_type)s
                                AND (
                                  (pd.id IS NOT NULL AND
                                      pd.max_date <= %(date_end)s) OR
                                  (pc.id IS NOT NULL AND
                                      pc.max_date <= %(date_end)s) OR
                                  (pd.id IS NULL AND pc.id IS NULL)
                                ) AND l.date <= %(date_end)s AND m.state IN ('posted')
            GROUP BY l.id, l.partner_id, m.name, l.date, l.date_maturity, l.name,
                CASE WHEN l.ref IS NOT NULL
                    THEN l.ref
                    ELSE m.ref
                END,
                l.blocked, l.currency_id, l.balance, l.amount_currency, l.company_id
        """

        params = {
            'partners': tuple(partners),
            'account_type': account_type,
            'date_end': date_end,
        }

        self._cr.execute(query, params)
        result_dict = self._cr.dictfetchall()

        print(result_dict,'resulttttttttttttttttttttttttttt')

        # print(data,'dataaaaaaaaaaaaaa')
        # lines = self.env['account.move.line'].search(
        #     [('date_maturity', '<=', self.date_end), ('partner_id', '=', self.partner_id.id),
        #      ('full_reconcile_id', '=', False),
        #      ('balance', '!=', 0), ('account_id.reconcile', '=', True),
        #      ('move_id.state', '=', 'posted')], order='date_maturity ASC')
        # lines = self.env['account.move'].search(
        #     [('invoice_date', '<=', self.date_end), ('partner_id', '=', self.partner_id.id),
        #      ('state', '=', 'posted')], order='invoice_date ASC')

        # partner_data = data.get("data", {}).get(self.partner_id.id, {})
        # print(partner_data,'partnewrdddddddd')
        # for line in lines:
        #     print(line.name)

        l_list = []

        align_left = workbook.add_format(
            {'font_size': 9, 'valign': 'vcenter', 'align': 'left'})
        align_left_bg = workbook.add_format(
            {'font_size': 9, 'bold': True, 'valign': 'vcenter', 'align': 'left','border':1 })
        align_right_bg = workbook.add_format(
            {'font_size': 9, 'bold': True, 'valign': 'vcenter', 'align': 'right', })
        align = workbook.add_format(
            {'bold': True, 'font_size': 9, 'valign': 'vcenter', 'align': 'left'})
        row = 0
        date_style = workbook.add_format(
            {'align': 'center', 'font_size': 9, 'num_format': 'dd/mm/yyyy',
             'valign': 'vcenter', })
        date_style_bold = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': 9, 'num_format': 'dd/mm/yyyy',
             'valign': 'vcenter', })
        sheet.merge_range(row, 7,row,0, "Statement of Account from"+ " "+self.company_id.name, align_left_bg)
        sheet.write('B2', 'Date:', align_left_bg)
        sheet.write('C2', self.date_end, align)
        sheet.write('B5', 'statement To:', align_left_bg)
        sheet.write('C5', self.partner_id.name, align)
        sheet.write('E5', 'VAT:', align_left_bg)
        sheet.write('F5', self.partner_id.vat, align)
        sheet.write('B6', 'statement From:', align_left_bg)
        sheet.write('C6', self.company_id.name, align)
        sheet.write('E6', 'VAT:', align_left_bg)
        sheet.write('F6', self.company_id.vat, align)
        sheet.merge_range('A9:I9',' Statement up to'+ str(self.date_end) + 'in AED', align_right_bg)
        row = 10
        sheet.write('A10', 'Date', align_left_bg)
        sheet.merge_range('B10:C10', 'PO NO/Description', align_left_bg)
        sheet.merge_range('D10:E10', 'Source Document', align_left_bg)
        sheet.merge_range('F10:I10', 'Against', align_left_bg)
        sheet.write('J10', 'Debit Amt', align_left_bg)
        sheet.write('K10', 'Credit Amt', align_left_bg)
        sheet.write('L10', 'Balance Amt', align_left_bg)
        row = 11

        if result_dict:
            current = 0
            b_1_30 = 0
            b_30_60 = 0
            b_60_90 = 0
            b_90_120 = 0
            b_over_120 = 0
            for rec in result_dict:
                _bucket_dates = {
                    'today': fields.date.today(),
                    'minus_30': fields.date.today() - timedelta(days=30),
                    'minus_60': fields.date.today() - timedelta(days=60),
                    'minus_90': fields.date.today() - timedelta(days=90),
                    'minus_120': fields.date.today() - timedelta(days=120),
                }
                print(rec,'reccccccccccccccccccc')
                if rec['date'] >= _bucket_dates['today']:
                    current += rec['balance']
                elif rec['date'] >= _bucket_dates['minus_30']:
                    b_1_30 += rec['balance']
                elif rec['date'] >= _bucket_dates['minus_60']:
                    b_30_60 += rec['balance']
                elif rec['date'] >= _bucket_dates['minus_90']:
                    b_60_90 +=rec['balance']
                elif rec['date'] >= _bucket_dates['minus_120']:
                    b_90_120 += rec['balance']
                else:
                    b_over_120 += rec['balance']
                due = rec['credit']
                l_list.append(
                    {
                        'date': rec['date'],
                        'name': rec['move_id'],
                        'desc': rec['name'],
                        'debit': rec['debit'],
                        'credit': rec['open_amount'],
                        'balance': rec['balance'],

                    }
                )
                data = {
                    'date_end': self.date_end,
                    'company_id': self.company_id.id,
                    'partner_ids': self.partner_id.id,
                    'record': l_list,
                    'bucket': self.show_aging_buckets,
                    'current': current,
                    'b_1_30': b_1_30,
                    'b_30_60': b_30_60,
                    'b_60_90': b_60_90,
                    'b_90_120': b_90_120,
                    'b_over_120': b_over_120,
                    "due": due
                }
                print(data['current'],'fffffffffffffffffffffffffffffff')
                print(data['record'][0]['date'],'llllllllllllllllllllllllllllllll')
                # print(data['record'][0]['name'],'llllllllllllllllllllllllllllllll')
                for datas in data['record']:

                    move_record = self.env['account.move'].search([('name', '=', datas['name'])])
                    picking = ''
                    if move_record.picking_id.name:
                        picking = move_record.picking_id.name

                    print(data,'cccccccccccccccccccccccccc')

                    sheet.write('A'+str(row),datas['date'],date_style)
                    # sheet.write('F'+str(row),data['desc'],date_style)
                    sheet.write('J'+str(row),datas['debit'],align_left)
                    sheet.write('K'+str(row),datas['credit'],align_left)
                    sheet.write('L'+str(row),datas['balance'],align_left)
                    sheet.merge_range('B'+str(row)+':'+'C'+str(row),datas['name'],align_left)
                    sheet.merge_range('D'+str(row)+':'+'E'+str(row),picking,align_left)
                    sheet.merge_range('F'+str(row)+':'+'I'+str(row),datas['desc'],align_left)
                # sheet.write('A'+str(row),data['record'][0]['date'],date_style)
                # sheet.write('A'+str(row),data['record'][0]['date'],date_style)
                # sheet.write('A'+str(row),data['record'][0]['date'],date_style)
                row+=1

        if self.show_aging_buckets:
            print(data, 'kkkkkkkkkkkkkkkkkkk')
            """for aging bucket"""
            sheet.write(row, 2, 'Current Due', align)
            sheet.write(row, 3, '1-30 Days Due', align)
            sheet.write(row, 4, '30-60 Days Due', align)
            sheet.write(row, 5, '60-90 Days Due', align)
            sheet.write(row, 6, '90-120 Days Due', align)
            sheet.write(row, 7, '+120 Days Due', align)
            sheet.write(row, 8, 'Balance Due', align)
            sheet.write(row + 1, 2, "{:.2f}".format(data['current']), align_left)
            sheet.write(row + 1, 3, "{:.2f}".format(data['b_1_30']), align_left)
            sheet.write(row + 1, 4, "{:.2f}".format(data['b_30_60']), align_left)
            sheet.write(row + 1, 5, "{:.2f}".format(data['b_60_90']), align_left)
            sheet.write(row + 1, 6, "{:.2f}".format(data['b_90_120']), align_left)
            sheet.write(row + 1, 7, "{:.2f}".format(data['b_over_120']), align_left)
            sheet.write(row + 1, 8, "{:.2f}".format(data['due']), align_left)
