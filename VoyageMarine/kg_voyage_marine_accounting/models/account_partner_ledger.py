# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.tools import get_lang


class AccountPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger.report.handler"

    def _get_aml_values(self, options, partner_ids, offset=0, limit=None):
        rslt = {partner_id: [] for partner_id in partner_ids}

        partner_ids_wo_none = [x for x in partner_ids if x]
        directly_linked_aml_partner_clauses = []
        directly_linked_aml_partner_params = []
        indirectly_linked_aml_partner_params = []
        indirectly_linked_aml_partner_clause = 'aml_with_partner.partner_id IS NOT NULL'

        if None in partner_ids:
            directly_linked_aml_partner_clauses.append('account_move_line.partner_id IS NULL')

        if partner_ids_wo_none:
            directly_linked_aml_partner_clauses.append(
                'account_move_line.partner_id IN %s'
            )
            directly_linked_aml_partner_params.append(tuple(partner_ids_wo_none))
            indirectly_linked_aml_partner_clause = 'aml_with_partner.partner_id IN %s'
            indirectly_linked_aml_partner_params.append(tuple(partner_ids_wo_none))

        directly_linked_aml_partner_clause = '(' + ' OR '.join(directly_linked_aml_partner_clauses) + ')'

        ct_query = self.env['account.report']._get_query_currency_table(options)
        queries = []
        all_params = []

        lang = self.env.lang or get_lang(self.env).code

        journal_name = (
            f"COALESCE(journal.name->>'{lang}', journal.name->>'en_US')"
            if self.pool['account.journal'].name.translate else 'journal.name'
        )

        account_name = (
            f"COALESCE(account.name->>'{lang}', account.name->>'en_US')"
            if self.pool['account.account'].name.translate else 'account.name'
        )

        # Selection mapping
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
            END AS code_value
        """

        report = self.env.ref('account_reports.partner_ledger_report')

        for column_group_key, group_options in report._split_options_per_column_group(options).items():
            tables, where_clause, where_params = report._query_get(group_options, 'strict_range')

            all_params += [
                column_group_key,
                *where_params,
                *directly_linked_aml_partner_params,
                column_group_key,
                *indirectly_linked_aml_partner_params,
                *where_params,
                group_options['date']['date_from'],
                group_options['date']['date_to'],
            ]

            # --------------------------------------------------
            # DIRECT LINES
            # --------------------------------------------------
            queries.append(f"""
                SELECT
                    account_move_line.id,
                    NULL AS partial_id,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.code,
                    {code_case},
                    division.name AS division,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    account_move_line.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    ROUND(account_move_line.debit * currency_table.rate, currency_table.precision) AS debit,
                    ROUND(account_move_line.credit * currency_table.rate, currency_table.precision) AS credit,
                    ROUND(account_move_line.balance * currency_table.rate, currency_table.precision) AS balance,
                    account_move.name AS move_name,
                    account_move.move_type,
                    account.code AS account_code,
                    {account_name} AS account_name,
                    journal.code AS journal_code,
                    {journal_name} AS journal_name,
                    %s AS column_group_key,
                    'directly_linked_aml' AS key
                FROM {tables}
                JOIN account_move ON account_move.id = account_move_line.move_id
                LEFT JOIN kg_divisions division ON division.id = account_move.division_id
                LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id
                LEFT JOIN account_account account ON account.id = account_move_line.account_id
                LEFT JOIN account_journal journal ON journal.id = account_move_line.journal_id
                WHERE {where_clause}
                  AND {directly_linked_aml_partner_clause}
                ORDER BY account_move_line.date, account_move_line.id
            """)

            # --------------------------------------------------
            # INDIRECT (RECONCILED) LINES
            # --------------------------------------------------
            queries.append(f"""
                SELECT
                    account_move_line.id,
                    partial.id AS partial_id,
                    account_move_line.date_maturity,
                    account_move_line.name,
                    account_move_line.code,
                    {code_case},
                    division.name AS division,
                    account_move_line.ref,
                    account_move_line.company_id,
                    account_move_line.account_id,
                    account_move_line.payment_id,
                    aml_with_partner.partner_id,
                    account_move_line.currency_id,
                    account_move_line.amount_currency,
                    account_move_line.matching_number,
                    COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                    CASE
                        WHEN aml_with_partner.balance > 0 THEN 0
                        ELSE ROUND(partial.amount * currency_table.rate, currency_table.precision)
                    END AS debit,
                    CASE
                        WHEN aml_with_partner.balance < 0 THEN 0
                        ELSE ROUND(partial.amount * currency_table.rate, currency_table.precision)
                    END AS credit,
                    -sign(aml_with_partner.balance)
                        * ROUND(partial.amount * currency_table.rate, currency_table.precision) AS balance,
                    account_move.name AS move_name,
                    account_move.move_type,
                    account.code AS account_code,
                    {account_name} AS account_name,
                    journal.code AS journal_code,
                    {journal_name} AS journal_name,
                    %s AS column_group_key,
                    'indirectly_linked_aml' AS key
                FROM {tables}
                LEFT JOIN {ct_query} ON currency_table.company_id = account_move_line.company_id,
                account_partial_reconcile partial,
                account_move,
                account_move_line aml_with_partner,
                account_journal journal,
                account_account account,
                kg_divisions division
                WHERE
                    (account_move_line.id = partial.debit_move_id
                     OR account_move_line.id = partial.credit_move_id)
                    AND account_move_line.partner_id IS NULL
                    AND account_move.id = account_move_line.move_id
                    AND division.id = account_move.division_id
                    AND (aml_with_partner.id = partial.debit_move_id
                         OR aml_with_partner.id = partial.credit_move_id)
                    AND {indirectly_linked_aml_partner_clause}
                    AND journal.id = account_move_line.journal_id
                    AND account.id = account_move_line.account_id
                    AND {where_clause}
                    AND partial.max_date BETWEEN %s AND %s
                ORDER BY account_move_line.date, account_move_line.id
            """)

        query = '(' + ') UNION ALL ('.join(queries) + ')'

        if offset:
            query += ' OFFSET %s'
            all_params.append(offset)

        if limit:
            query += ' LIMIT %s'
            all_params.append(limit)

        self._cr.execute(query, all_params)

        for aml_result in self._cr.dictfetchall():
            aml_result.setdefault('partial_id', None)

            if aml_result['key'] == 'indirectly_linked_aml':
                if aml_result['partner_id'] in rslt:
                    rslt[aml_result['partner_id']].append(aml_result)
                if None in rslt:
                    rslt[None].append({
                        **aml_result,
                        'debit': aml_result['credit'],
                        'credit': aml_result['debit'],
                        'balance': -aml_result['balance'],
                    })
            else:
                rslt[aml_result['partner_id']].append(aml_result)

        return rslt
