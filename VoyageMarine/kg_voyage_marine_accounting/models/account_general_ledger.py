# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api, _
from odoo.tools.misc import format_date
from odoo.tools import get_lang
from odoo.exceptions import UserError

from datetime import timedelta
from collections import defaultdict


class GeneralLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'

    def _get_query_amls(self, report, options, expanded_account_ids, offset=0, limit=None):
        """
        Construct a query retrieving the account.move.lines when expanding a general ledger line.
        Adds:
            - code (selection)
            - division (many2one)
        """
        additional_domain = [('account_id', 'in', expanded_account_ids)] if expanded_account_ids else None
        queries = []
        all_params = []

        lang = self.env.user.lang or get_lang(self.env).code

        journal_name = (
            f"COALESCE(journal.name->>'{lang}', journal.name->>'en_US')"
            if self.pool['account.journal'].name.translate else 'journal.name'
        )
        account_name = (
            f"COALESCE(account.name->>'{lang}', account.name->>'en_US')"
            if self.pool['account.account'].name.translate else 'account.name'
        )

        # --------------------------------------------------
        # Selection mapping for CODE (same as Partner Ledger)
        # --------------------------------------------------
        code_case = """
            CASE
                WHEN account_move_line.code = 'ds' THEN 'DS'
                WHEN account_move_line.code = 'ms' THEN 'MS'
                WHEN account_move_line.code = 'os' THEN 'OS'
                WHEN account_move_line.code = 'rs' THEN 'RS'
                WHEN account_move_line.code = 'fl' THEN 'FL'
                WHEN account_move_line.code = 'fs' THEN 'FS'
                WHEN account_move_line.code = 'sl' THEN 'SL'
                WHEN account_move_line.code = 'ss' THEN 'SS'
                WHEN account_move_line.code = 'nl' THEN 'NL'
                WHEN account_move_line.code = 'ns' THEN 'NS'
                WHEN account_move_line.code = 'pl' THEN 'PL'
                WHEN account_move_line.code = 'ps' THEN 'PS'
                WHEN account_move_line.code = 'cl' THEN 'CL'
                WHEN account_move_line.code = 'cs' THEN 'CS'
                WHEN account_move_line.code = 'tr' THEN 'TR'
                WHEN account_move_line.code = 'ml' THEN 'ML'
                WHEN account_move_line.code = 'tl' THEN 'TL'
                WHEN account_move_line.code = 'rl' THEN 'RL'
                WHEN account_move_line.code = 'el' THEN 'EL'
                WHEN account_move_line.code = 'sm' THEN 'SM'
                WHEN account_move_line.code = 'fm' THEN 'FM'
                WHEN account_move_line.code = 'lm' THEN 'LM'
                WHEN account_move_line.code = 'nm' THEN 'NM'
                WHEN account_move_line.code = 'cm' THEN 'CM'
                WHEN account_move_line.code = 'rm' THEN 'RM'
                WHEN account_move_line.code = 'pm' THEN 'PM'
                WHEN account_move_line.code = 'om' THEN 'OM'
                WHEN account_move_line.code = 'mm' THEN 'MM'
                WHEN account_move_line.code = 'es' THEN 'ES'
                ELSE account_move_line.code
            END
        """

        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            tables, where_clause, where_params = report._query_get(
                group_options,
                domain=additional_domain,
                date_scope='strict_range'
            )
            ct_query = report._get_query_currency_table(group_options)

            queries.append(f"""
                (
                SELECT
                    account_move_line.id,
                    account_move_line.date,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,

                    -- ✅ CUSTOM FIELDS
                    {code_case} AS code,
                    division.name AS division,

                    ROUND(account_move_line.debit * currency_table.rate, currency_table.precision)   AS debit,
                    ROUND(account_move_line.credit * currency_table.rate, currency_table.precision)  AS credit,
                    ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,

                    move.name                   AS move_name,
                    company.currency_id         AS company_currency_id,
                    partner.name                AS partner_name,
                    move.move_type              AS move_type,
                    account.code                AS account_code,
                    {account_name}              AS account_name,
                    journal.code                AS journal_code,
                    {journal_name}              AS journal_name,
                    full_rec.id                 AS full_rec_name,

                    %s AS column_group_key
                FROM {tables}
                JOIN account_move move ON move.id = account_move_line.move_id
                LEFT JOIN kg_divisions division ON division.id = move.division_id
                LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN res_company company ON company.id = account_move_line.company_id
                LEFT JOIN res_partner partner ON partner.id = account_move_line.partner_id
                LEFT JOIN account_account account ON account.id = account_move_line.account_id
                LEFT JOIN account_journal journal ON journal.id = account_move_line.journal_id
                LEFT JOIN account_full_reconcile full_rec ON full_rec.id = account_move_line.full_reconcile_id
                WHERE {where_clause}
                ORDER BY account_move_line.date, account_move_line.id
                )
            """)

            all_params.append(column_group_key)
            all_params += where_params

        full_query = " UNION ALL ".join(queries)

        if offset:
            full_query += " OFFSET %s"
            all_params.append(offset)

        if limit:
            full_query += " LIMIT %s"
            all_params.append(limit)

        return full_query, all_params
