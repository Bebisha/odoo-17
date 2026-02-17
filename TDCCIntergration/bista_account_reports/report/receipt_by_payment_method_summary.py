# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from odoo import models, api, _
# from odoo.exceptions import Warning
from datetime import datetime
import warnings

from odoo.exceptions import UserError


class AccountPaymentReport(models.AbstractModel):
    _name = 'report.bista_account_reports.report_bypaymentmethodsummary'
    _description = 'TDCC Account Reports'

    def _get_data_from_report(self, data):
        dt1 = data.get('start_date')
        dt2 = data.get('end_date')
        account_payments = self.env['account.payment'].search([
            ('state', '!=', 'cancelled'),
            ('payment_type', '=', 'inbound'),
            ('date', '>=', dt1),
            ('date', '<=', dt2)
        ])
        if data.get('service_type_ids'):
            service_type_ids = data.get('service_type_ids')
            account_payments = account_payments.filtered(lambda p: p.service_type_id.id in service_type_ids)

        if data.get('client_id'):
            client_id = data.get('client_id')
            account_payments = account_payments.filtered(lambda p: p.partner_id.id == client_id)
        payment_summary = {}
        for payment in account_payments:
            payment_method = payment.journal_id.name
            payment_summary[payment_method] = payment_summary.get(payment_method, 0) + payment.amount

        result = [
            {'payment_method': method, 'amount': amount}
            for method, amount in payment_summary.items()
        ]
        return result

    def _get_title(self, data):
        new_st_dt = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        new_end_dt = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        dt_str = new_st_dt.strftime('%d-%m-%Y ')
        end_dt_str = new_end_dt.strftime('%d-%m-%Y ')
        return "Receipts for the period %s to %s" % (dt_str, end_dt_str)

    @api.model
    def _get_report_values(self, docids, data=None):
        payment_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_account_reports.report_payment_method_summary')
        return {
            'doc_ids': self.ids,
            'docs': self,
            'get_title': self._get_title(data['form_data']),
            'doc_model': payment_report.model,
            'clients': data['form_data']['client_id'],
            'report_type': data['form_data']['report_type'],
            'get_data_from_report': self._get_data_from_report(
                data['form_data']),

        }
