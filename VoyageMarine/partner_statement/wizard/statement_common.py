# Copyright 2018 Graeme Gellatly
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from base64 import encodebytes
from datetime import datetime, timedelta
from io import BytesIO

import xlsxwriter
from dateutil.relativedelta import relativedelta
import io

from odoo import api, fields, models
from odoo.exceptions import ValidationError


# class ResPartnerInherit(models.Model):
#     _inherit = "res.partner"
#
#     store_total_due = fields.Monetary(store=True)

    # @api.depends('unreconciled_aml_ids', 'followup_next_action_date')
    # @api.depends_context('company', 'allowed_company_ids')
    # def _compute_total_due(self):
    #     for partner in self:
    #         total_due = 0
    #         for aml in partner.unreconciled_aml_ids:
    #             if self.env.company in aml.company_id.parent_ids and not aml.blocked:
    #                 total_due += aml.amount_residual
    #         partner.store_total_due = total_due


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
    partner_id = fields.Many2one('res.partner', 'Partner')
    date_end = fields.Date(required=True, default=fields.Date.context_today)
    show_aging_buckets = fields.Boolean(string="Show Aging Bucket", default=True)
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

    # liabilit_payable_partner_ids = fields.Many2many(
    #     'res.partner',
    #     'new_liabilit_payable_partner_rel',
    #     'new_liabilit_wizard_id',
    #     'new_liabilit_partner_id',
    #     string='liability Payable Partners'
    # )

    @api.onchange("aging_type")
    def onchange_aging_type(self):
        if self.aging_type == "months":
            self.date_end = fields.Date.context_today(self).replace(
                day=1
            ) - relativedelta(days=1)
        else:
            self.date_end = fields.Date.context_today(self)

    asset_receivable_partner_ids = fields.Many2many('res.partner', string='Asset Receivable Partners')

    @api.model
    def default_get(self, fields_list):
        res = super(StatementCommon, self).default_get(fields_list)
        date_end = res.get('date_end')
        account_type = res.get('account_type', 'asset_receivable')

        if date_end:
            if account_type == 'asset_receivable':
                query = """
                    SELECT DISTINCT aml.partner_id
                    FROM account_move_line aml
                    JOIN account_account aa ON aml.account_id = aa.id
                    WHERE aa.account_type = 'asset_receivable'
                    AND aml.date <= %s
                    AND aml.partner_id IS NOT NULL
                """
                self.env.cr.execute(query, (date_end,))
                result = self.env.cr.fetchall()
                partner_ids = [row[0] for row in result if row[0]]
                res['asset_receivable_partner_ids'] = [(6, 0, partner_ids)]

            elif account_type == 'liability_payable':
                query = """
                    SELECT DISTINCT aml.partner_id
                    FROM account_move_line aml
                    JOIN account_account aa ON aml.account_id = aa.id
                    WHERE aa.account_type = 'liability_payable'
                    AND aml.date <= %s
                    AND aml.partner_id IS NOT NULL
                """
                self.env.cr.execute(query, (date_end,))
                result = self.env.cr.fetchall()
                partner_ids = [row[0] for row in result if row[0]]
                res['asset_receivable_partner_ids'] = [(6, 0, partner_ids)]

        return res

    @api.onchange('account_type', 'date_end')
    def _onchange_account_type(self):
        if self.date_end:
            if self.account_type == 'asset_receivable':
                query = """
                    SELECT DISTINCT aml.partner_id
                    FROM account_move_line aml
                    JOIN account_account aa ON aml.account_id = aa.id
                    WHERE aa.account_type = 'asset_receivable'
                    AND aml.date <= %s
                    AND aml.partner_id IS NOT NULL
                """
                self.env.cr.execute(query, (self.date_end,))
                result = self.env.cr.fetchall()
                self.asset_receivable_partner_ids = [(6, 0, [row[0] for row in result if row[0]])]

            elif self.account_type == 'liability_payable':
                query = """
                    SELECT DISTINCT aml.partner_id
                    FROM account_move_line aml
                    JOIN account_account aa ON aml.account_id = aa.id
                    WHERE aa.account_type = 'liability_payable'
                    AND aml.date <= %s
                    AND aml.partner_id IS NOT NULL
                """
                self.env.cr.execute(query, (self.date_end,))
                result = self.env.cr.fetchall()
                self.asset_receivable_partner_ids = [(6, 0, [row[0] for row in result if row[0]])]

    def get_default_partner_ids_report(self):
        if self._context.get('active_ids'):
            return self._context['active_ids']
        elif self.partner_id:
            return [self.partner_id.id]
        else:
            return self.asset_receivable_partner_ids.ids[:100]

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
        # if not self.partner_id:
        #     raise ValidationError("If you wish to continue this process, please select a partner.")
        if not self.env.company.bank_ids:
            raise ValidationError("Please enter bank details for the company.")
        if self.partner_id:
            if not self.partner_id.street:
                raise ValidationError("Please enter the partner's address.")

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

        self.generate_xlsx_report(workbook, data=data, date_end=self.date_end, partners=self.partner_id.ids,
                                  account_type=self.account_type)

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

    def _display_lines_sql_q1(self, partners, date_end, account_type):
        partners = tuple(partners)
        # print(partners,'partnerssssssssssssssssssssss')
        return str(
            self._cr.mogrify(
                """
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
                                ) AND l.date <= %(date_end)s AND m.state IN ('posted') AND (m.pdc_id IS NULL )
            GROUP BY l.id, l.partner_id, m.name, l.date, l.date_maturity, l.name,
                CASE WHEN l.ref IS NOT NULL
                    THEN l.ref
                    ELSE m.ref
                END,
                l.blocked, l.currency_id, l.balance, l.amount_currency, l.company_id
            """,
                locals(),
            ),
            "utf-8",
        )

    def _display_lines_sql_q2(self):
        return str(
            self._cr.mogrify(
                """
                SELECT Q1.partner_id, Q1.currency_id, Q1.move_id,
                    Q1.date, Q1.date_maturity, Q1.debit, Q1.credit,
                    Q1.name, Q1.ref, Q1.blocked, Q1.company_id,Q1.balance,
                CASE WHEN Q1.currency_id is not null
                    THEN Q1.open_amount_currency
                    ELSE Q1.open_amount
                END as open_amount
                FROM Q1
                """,
                locals(),
            ),
            "utf-8",
        )

    def _display_lines_sql_q3(self, company_id):
        return str(
            self._cr.mogrify(
                """
            SELECT Q2.partner_id, Q2.move_id, Q2.date, Q2.date_maturity,
              Q2.name, Q2.ref, Q2.debit, Q2.credit,
              Q2.debit-Q2.credit AS amount, blocked,
              COALESCE(Q2.currency_id, c.currency_id) AS currency_id,
              Q2.open_amount,Q2.balance
            FROM Q2
            JOIN res_company c ON (c.id = Q2.company_id)
            WHERE c.id = %(company_id)s AND Q2.open_amount != 0.0
            """,
                locals(),
            ),
            "utf-8",
        )

    def _show_buckets_sql_q2(self, date_end, minus_30, minus_60, minus_90):
        return str(
            self._cr.mogrify(
                """
            SELECT partner_id, currency_id, date_maturity, open_due,
                open_due_currency, move_id, company_id,
            CASE
                WHEN %(date_end)s <= date_maturity AND currency_id is null
                    THEN open_due
                WHEN %(date_end)s <= date_maturity AND currency_id is not null
                    THEN open_due_currency
                ELSE 0.0
            END as current,
            CASE
                WHEN %(minus_30)s < date_maturity
                    AND date_maturity < %(date_end)s
                    AND currency_id is null
                THEN open_due
                WHEN %(minus_30)s < date_maturity
                    AND date_maturity < %(date_end)s
                    AND currency_id is not null
                THEN open_due_currency
                ELSE 0.0
            END as b_1_30,
            CASE
                WHEN %(minus_60)s < date_maturity
                    AND date_maturity <= %(minus_30)s
                    AND currency_id is null
                THEN open_due
                WHEN %(minus_60)s < date_maturity
                    AND date_maturity <= %(minus_30)s
                    AND currency_id is not null
                THEN open_due_currency
                ELSE 0.0
            END as b_30_60,
            CASE
                WHEN %(minus_90)s < date_maturity
                    AND date_maturity <= %(minus_60)s
                    AND currency_id is null
                THEN open_due
                WHEN %(minus_90)s < date_maturity
                    AND date_maturity <= %(minus_60)s
                    AND currency_id is not null
                THEN open_due_currency
                ELSE 0.0
            END as b_60_90,
            
            CASE
                WHEN date_maturity <= %(minus_90)s
                    AND currency_id is null
                THEN open_due
                WHEN date_maturity <= %(minus_90)s
                    AND currency_id is not null
                THEN open_due_currency
                ELSE 0.0
            END as b_over_90
            FROM Q1
        """,
                locals(),
            ),
            "utf-8",
        )

    def _show_buckets_sql_q4(self):
        return """
            SELECT partner_id, currency_id, sum(current) as current,
                sum(b_1_30) as b_1_30, sum(b_30_60) as b_30_60,
                sum(b_60_90) as b_60_90, 
                sum(b_over_90) as b_over_90
            FROM Q3
            GROUP BY partner_id, currency_id
        """

    def _show_buckets_sql_q3(self, company_id):

        return str(
            self._cr.mogrify(
                """
            SELECT Q2.partner_id, current, b_1_30, b_30_60, b_60_90,
                                b_over_90,
            COALESCE(Q2.currency_id, c.currency_id) AS currency_id
            FROM Q2
            JOIN res_company c ON (c.id = Q2.company_id)
            WHERE c.id = %(company_id)s
        """,
                locals(),
            ),
            "utf-8",
        )

    def _show_buckets_sql_q1(self, partners, date_end, account_type):
        print(account_type, 'account_type')
        return str(
            self._cr.mogrify(
                """
            SELECT l.partner_id, l.currency_id, l.company_id, l.move_id,
            CASE WHEN l.balance > 0.0
                THEN l.balance - sum(coalesce(pd.amount, 0.0))
                ELSE l.balance + sum(coalesce(pc.amount, 0.0))
            END AS open_due,
            CASE WHEN l.balance > 0.0
                THEN l.amount_currency - sum(coalesce(pd.debit_amount_currency, 0.0))
                ELSE l.amount_currency + sum(coalesce(pc.credit_amount_currency, 0.0))
            END AS open_due_currency,
                 l.date
             as date_maturity
            FROM account_move_line l
            JOIN account_move m ON (l.move_id = m.id)
            JOIN account_account aa ON (aa.id = l.account_id)
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
                                ) AND l.date <= %(date_end)s AND not l.blocked
                                  AND m.state IN ('posted')
            GROUP BY l.partner_id, l.currency_id, l.date, l.date_maturity,
                                l.amount_currency, l.balance, l.move_id,
                                l.company_id, l.id
        """,
                locals(),
            ),
            "utf-8",
        )

    def _get_bucket_dates(self, date_end, aging_type):
        print(getattr(
            self, "_get_bucket_dates_%s" % aging_type, self._get_bucket_dates_days
        )(date_end), 'pppppppppp')
        return getattr(
            self, "_get_bucket_dates_%s" % aging_type, self._get_bucket_dates_days
        )(date_end)

    def _get_bucket_dates_months(self, date_end):
        res = {}
        d = date_end
        for k in ("date_end", "minus_30", "minus_60", "minus_90"):
            res[k] = d
            d = d.replace(day=1) - timedelta(days=1)
        return res

    def _get_bucket_dates_days(self, date_end):
        return {
            "date_end": date_end,
            "minus_30": date_end - timedelta(days=30),
            "minus_60": date_end - timedelta(days=60),
            "minus_90": date_end - timedelta(days=90),
        }

    def _get_account_show_buckets(
            self, company_id, partner_ids, date_end, account_type, aging_type
    ):
        buckets = dict(map(lambda x: (x, []), partner_ids))
        partners = tuple(partner_ids)
        full_dates = self._get_bucket_dates(date_end, aging_type)
        # pylint: disable=E8103
        # All input queries are properly escaped - false positive
        self.env.cr.execute(
            """
            WITH Q1 AS (%s),
                Q2 AS (%s),
                Q3 AS (%s),
                Q4 AS (%s)
            SELECT partner_id, currency_id, current, b_1_30, b_30_60, b_60_90,
                 b_over_90,
                current+b_1_30+b_30_60+b_60_90+b_over_90
                AS balance
            FROM Q4
            GROUP BY partner_id, currency_id, current, b_1_30, b_30_60,
                b_60_90, b_over_90"""
            % (
                self._show_buckets_sql_q1(partners, date_end, account_type),
                self._show_buckets_sql_q2(
                    full_dates["date_end"],
                    full_dates["minus_30"],
                    full_dates["minus_60"],
                    full_dates["minus_90"],
                ),
                self._show_buckets_sql_q3(company_id),
                self._show_buckets_sql_q4(),
            )
        )

        for row in self.env.cr.dictfetchall():
            buckets[row.pop("partner_id")].append(row)
        return buckets

    def generate_xlsx_report(self, workbook, data, date_end, partners, account_type, objs=None):
        """For generating XLSX report"""
        sheet = workbook.add_worksheet('General Ledger Report')

        # get bucket values
        buckets = self._get_account_show_buckets(self.company_id.id, partners, date_end, account_type, self.aging_type)
        self.env.cr.execute(
            """
            WITH Q1 as (%s),
                 Q2 AS (%s),
                 Q3 AS (%s)
            SELECT partner_id, currency_id, move_id, date, date_maturity, debit,
                   credit, amount, open_amount, name, ref, blocked,balance
            FROM Q3
            ORDER BY date, date_maturity, move_id"""
            % (
                self._display_lines_sql_q1(partners, date_end, account_type),
                self._display_lines_sql_q2(),
                self._display_lines_sql_q3(self.company_id.id),
            )
        )

        # fetched_data = self.env.cr.dictfetchall()

        # query = """
        #     SELECT l.id, m.name AS move_id, l.partner_id, l.date, l.name,
        #         l.blocked, l.currency_id, l.company_id,l.balance,
        #         CASE WHEN l.ref IS NOT NULL
        #             THEN l.ref
        #             ELSE m.ref
        #         END as ref,
        #         CASE WHEN (l.currency_id is not null AND l.amount_currency > 0.0)
        #             THEN avg(l.amount_currency)
        #             ELSE avg(l.debit)
        #         END as debit,
        #         CASE WHEN (l.currency_id is not null AND l.amount_currency < 0.0)
        #             THEN avg(l.amount_currency * (-1))
        #             ELSE avg(l.credit)
        #         END as credit,
        #         CASE WHEN l.balance > 0.0
        #             THEN l.balance - sum(coalesce(pd.amount, 0.0))
        #             ELSE l.balance + sum(coalesce(pc.amount, 0.0))
        #         END AS open_amount,
        #         CASE WHEN l.balance > 0.0
        #             THEN l.amount_currency - sum(coalesce(pd.debit_amount_currency, 0.0))
        #             ELSE l.amount_currency + sum(coalesce(pc.credit_amount_currency, 0.0))
        #         END AS open_amount_currency,
        #         CASE WHEN l.date_maturity is null
        #             THEN l.date
        #             ELSE l.date_maturity
        #         END as date_maturity
        #     FROM account_move_line l
        #     JOIN account_account aa ON (aa.id = l.account_id)
        #     JOIN account_move m ON (l.move_id = m.id)
        #     LEFT JOIN (SELECT pr.*
        #         FROM account_partial_reconcile pr
        #         INNER JOIN account_move_line l2
        #         ON pr.credit_move_id = l2.id
        #         WHERE l2.date <= %(date_end)s
        #     ) as pd ON pd.debit_move_id = l.id
        #     LEFT JOIN (SELECT pr.*
        #         FROM account_partial_reconcile pr
        #         INNER JOIN account_move_line l2
        #         ON pr.debit_move_id = l2.id
        #         WHERE l2.date <= %(date_end)s
        #     ) as pc ON pc.credit_move_id = l.id
        #      WHERE l.partner_id IN %(partners)s AND aa.account_type = %(account_type)s
        #                         AND (
        #                           (pd.id IS NOT NULL AND
        #                               pd.max_date <= %(date_end)s) OR
        #                           (pc.id IS NOT NULL AND
        #                               pc.max_date <= %(date_end)s) OR
        #                           (pd.id IS NULL AND pc.id IS NULL)
        #                         ) AND l.date <= %(date_end)s AND m.state IN ('posted') AND (m.pdc_id IS NULL )
        #     GROUP BY l.id, l.partner_id, m.name, l.date, l.date_maturity, l.name,
        #         CASE WHEN l.ref IS NOT NULL
        #             THEN l.ref
        #             ELSE m.ref
        #         END,
        #         l.blocked, l.currency_id, l.balance, l.amount_currency, l.company_id
        # """
        #
        # params = {
        #     'partners': tuple(partners),
        #     'account_type': account_type,
        #     'date_end': date_end,
        # }
        #
        # self._cr.execute(query, params)
        result_dict = self._cr.dictfetchall()
        print(result_dict, "Balance Values for Debugging")
        # print(errr)

        l_list = []

        align_left = workbook.add_format(
            {'font_size': 9, 'valign': 'vcenter', 'align': 'left'})
        align_left_bg = workbook.add_format(
            {'font_size': 9, 'bold': True, 'valign': 'vcenter', 'align': 'left', 'border': 1})
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
        sheet.merge_range(row, 7, row, 0, "Statement of Account from" + " " + self.company_id.name, align_left_bg)
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
        sheet.merge_range('A9:I9', ' Statement up to' + str(self.date_end) + 'in AED', align_right_bg)
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
            cumulative_balance = 0
            credit_total = 0
            debit_total = 0
            for rec in result_dict:
                # _bucket_dates = {
                #     'today': fields.date.today(),
                #     'minus_30': fields.date.today() - timedelta(days=30),
                #     'minus_60': fields.date.today() - timedelta(days=60),
                #     'minus_90': fields.date.today() - timedelta(days=90),
                # }
                # if rec['date'] >= _bucket_dates['today']:
                #     current += rec['balance']
                # elif rec['date'] >= _bucket_dates['minus_30']:
                #     b_1_30 += rec['balance']
                # elif rec['date'] >= _bucket_dates['minus_60']:
                #     b_30_60 += rec['balance']
                # elif rec['date'] >= _bucket_dates['minus_90']:
                #     b_60_90 += rec['balance']
                # else:
                due = rec['credit']
                if rec["open_amount"] != 0:
                    cumulative_balance += rec['open_amount']
                    if rec["open_amount"] < 0:
                        rec["credit"] = rec["open_amount"]
                        rec["debit"] = 0.00
                        rec['balance'] = rec["open_amount"]
                        credit_total = credit_total + rec["open_amount"]
                    if rec["open_amount"] > 0:
                        rec["credit"] = 0.00
                        rec["debit"] = rec["open_amount"]
                        rec['balance'] = rec["open_amount"]
                        debit_total = debit_total + rec["open_amount"]
                    l_list.append(
                        {
                            'date': rec['date'],
                            'name': rec['move_id'],
                            'desc': rec['name'],
                            'debit': rec['debit'],
                            'credit': rec['credit'],
                            'balance': cumulative_balance,

                        }
                    )
                bucket_dict = buckets[self.partner_id.id]
                data = {
                    'date_end': self.date_end,
                    'company_id': self.company_id.id,
                    'partner_ids': self.partner_id.id,
                    'record': l_list,
                    'bucket': self.show_aging_buckets,
                    'current': bucket_dict[0].get('current'),
                    'b_1_30': bucket_dict[0].get('b_1_30'),
                    'b_30_60': bucket_dict[0].get('b_30_60'),
                    'b_60_90': bucket_dict[0].get('b_60_90'),
                    'b_over_90': bucket_dict[0].get('b_over_90'),
                    "due": cumulative_balance
                }
            #
            for datas in data['record']:
                move_record = self.env['account.move'].search([('name', '=', datas['name'])])
                picking = ''
                if move_record.picking_id.name:
                    picking = move_record.picking_id.name

                sheet.write('A' + str(row), datas['date'], date_style)
                # sheet.write('F'+str(row),data['desc'],date_style)
                sheet.write('J' + str(row), datas['debit'], align_left)
                sheet.write('K' + str(row), datas['credit'], align_left)
                sheet.write('L' + str(row), datas['balance'], align_left)
                sheet.merge_range('F' + str(row) + ':' + 'I' + str(row), datas['name'], align_left)
                sheet.merge_range('D' + str(row) + ':' + 'E' + str(row), picking, align_left)
                sheet.merge_range('B' + str(row) + ':' + 'C' + str(row), datas['desc'], align_left)
                # sheet.write('A'+str(row),data['record'][0]['date'],date_style)
                # sheet.write('A'+str(row),data['record'][0]['date'],date_style)
                # sheet.write('A'+str(row),data['record'][0]['date'],date_style)
                row += 1
            sheet.merge_range('F' + str(row) + ':' + 'I' + str(row), "Total Outstanding", align_left)
            sheet.write('J' + str(row), debit_total, align_left)
            sheet.write('K' + str(row), credit_total, align_left)
            sheet.write('L' + str(row), cumulative_balance, align_left)
            row += 1
            if self.show_aging_buckets:
                """for aging bucket"""
                sheet.write(row, 2, 'Current Due', align)
                sheet.write(row, 3, '1-30 Days Due', align)
                sheet.write(row, 4, '30-60 Days Due', align)
                sheet.write(row, 5, '60-90 Days Due', align)
                sheet.write(row, 7, '+90 Days Due', align)
                sheet.write(row, 8, 'Balance Due', align)
                sheet.write(row + 1, 2, "{:.2f}".format(data['current']), align_left)
                sheet.write(row + 1, 3, "{:.2f}".format(data['b_1_30']), align_left)
                sheet.write(row + 1, 4, "{:.2f}".format(data['b_30_60']), align_left)
                sheet.write(row + 1, 5, "{:.2f}".format(data['b_60_90']), align_left)
                sheet.write(row + 1, 7, "{:.2f}".format(data['b_over_90']), align_left)
                sheet.write(row + 1, 8, "{:.2f}".format(data['due']), align_left)
