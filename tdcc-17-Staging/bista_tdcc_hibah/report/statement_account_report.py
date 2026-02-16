# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, api, _
import warnings

from odoo.exceptions import UserError


class StatementAccount(models.AbstractModel):
    _name = 'report.bista_tdcc_hibah.report_account_statement_tdcc'
    _description = 'Statement of account Payment'

    def _get_data_from_report(self, data):
        partner_id = self.env['res.partner'].browse(
            int(data.get('partner_id')))
        if data.get('date', False):
            dt1 = data.get('date')
            where = "where am.move_type in ('out_invoice', 'out_refund') and \
                     am.amount_residual_signed != 0.00 and am.state = 'posted' \
                     and am.invoice_date <='" + dt1 + "' and am.partner_id = " \
                    + str(partner_id.id)
        query = """
                    select
                    am.name as number,
                    am.move_type as move_type,
                    to_char(am.invoice_date, 'DD/MM/YYYY') as date,
                    rp.name as client_name,
                    string_agg(aml.name, ',\n') as desc,
                    rp1.name as attendant,
                    am.amount_total_signed as total,
                    (am.amount_total_signed-am.amount_residual_signed) as receipts,
                    am.amount_residual_signed as balance
                from
                    account_move am
                    left join account_move_line aml on aml.move_id=am.id
                    left join res_partner rp on am.partner_id = rp.id
                    left join res_partner rp1 on
                    am.attendant_id=rp1.id """ + where + """
                group by
                    am.id,
                    rp.name,
                    rp1.name
                order by
                    am.invoice_date
                """
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        if not res:
            raise UserError(_("There is not data to print for this Client."))
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        statement_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_tdcc_hibah.report_account_statement_tdcc')
        partner_id = self.env['res.partner'].browse(
            data.get('form_data').get('partner_id'))
        return {
            'doc_ids': partner_id.ids,
            'docs': partner_id,
            'doc_model': statement_report.model,
            'date': data.get('form_data').get('date'),
            'partner': data['form_data']['partner_id'],
            'get_data_from_report': self._get_data_from_report(
                data.get('form_data')),
        }
