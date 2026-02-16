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
import  warnings

from odoo.exceptions import UserError


class AccountPaymentReport(models.AbstractModel):
    _name = 'report.bista_account_reports.report_bypaymentmethod'
    _description = 'TDCC Account Reports'

    def _get_data_from_report(self, data):
        dt1 = data.get('start_date')
        dt2 = data.get('end_date')
        if not dt1 or not dt2:
            raise ValueError(_("Start date and end date must be provided."))
        domain = [
            ('payment_type', '=', 'inbound'),
            ('state', '!=', 'cancelled'),
            ('date', '>=', dt1),
            ('date', '<=', dt2)
        ]
        client_id = data.get('client_id')
        service_type_ids = data.get('service_type_ids')
        if client_id:
            domain.append(('partner_id', '=', client_id))
        if service_type_ids:
            domain.append(('service_type_id', 'in', service_type_ids))
        account_payments = self.env['account.payment'].search(domain)
        if not account_payments:
            raise Warning(_("There is no data with the selected options."))
        result = {}
        for payment in account_payments:
            payment_method_id = payment.journal_id.id
            payment_date = payment.cheque_date if payment.journal_id.code == 'PDC' else payment.date
            payment_data = {
                'payment_method_id': payment_method_id,
                'receipt_number': payment.name,
                'client_name': payment.partner_id.name,
                'payment_date': payment_date.strftime('%d/%m/%Y') if payment_date else '',
                'payment_method': payment.journal_id.name,
                'amount': payment.amount
            }
            result.setdefault(payment_method_id, []).append(payment_data)

        return result

    def _get_title(self, data):
        new_st_dt = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        new_end_dt = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        dt_str = new_st_dt.strftime('%d-%m-%Y ')
        end_dt_str = new_end_dt.strftime('%d-%m-%Y ')
        if data.get('client'):
            return "Receipts for %s from %s to %s" % (data.get('client'),
                                                      dt_str, end_dt_str)
        else:
            return "Receipts from %s to %s" % (dt_str, end_dt_str)

    @api.model
    def _get_report_values(self, docids, data=None):
        payment_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_account_reports.report_by_paymentmethod')
        return {
            'doc_ids': self.ids,
            'docs': self,
            'get_title': self._get_title(data['form_data']),
            'doc_model': payment_report.model,
            'clients': data['form_data']['client_id'],
            'client_name': data['form_data']['client'],
            'report_type': data['form_data']['report_type'],
            'get_data_from_report': self._get_data_from_report(
                data['form_data']),

        }
