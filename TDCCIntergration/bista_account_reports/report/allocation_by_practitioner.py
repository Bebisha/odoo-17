# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from odoo import models, api, _
from datetime import datetime
import pytz

from odoo.exceptions import UserError


class AccountReportAllocationPractitioner(models.AbstractModel):
    _name = 'report.bista_account_reports.allocation_by_practitioner'
    _description = 'TDCC Account Report for allocation by practitioner'

    def _get_data_from_report(self, data):
        dt1 = data['start_date']
        dt2 = data['end_date']
        utz = self.env.user.tz or 'UTC'
        tz = pytz.timezone(utz)
        dt1 = datetime.strptime(dt1, '%Y-%m-%d').replace(tzinfo=pytz.utc).astimezone(tz)
        dt2 = datetime.strptime(dt2, '%Y-%m-%d').replace(tzinfo=pytz.utc).astimezone(tz)
        where = [
            ('physician_type', '=', 'single'),
            ('state', 'in', ['posted', 'reconciled']),
            ('date', '>=', dt1),
            ('date', '<=', dt2),
            ('amount', '>', 0)
        ]
        where1 = [
            ('physician_type', '=', 'multi'),
            ('state', 'in', ['posted', 'reconciled']),
            ('date', '>=', dt1),
            ('date', '<=', dt2),
            ('amount', '>', 0)
        ]
        if data['phy_id']:
            where.append(('physician_id', '=', data['phy_id']))
            where1.append(('physician_id', '=', data['phy_id']))
        elif data['code_id']:
            physician_ids = self.env['res.partner'].search([('physician_code_id', '=', data['code_id'])])
            if len(physician_ids) == 1:
                where.append(('physician_id', '=', physician_ids[0].id))
                where1.append(('physician_id', '=', physician_ids[0].id))
            elif len(physician_ids) > 1:
                where.append(('physician_id', 'in', physician_ids.ids))
                where1.append(('physician_id', 'in', physician_ids.ids))
        single_physician_payments = self.env['account.payment'].search(where)
        multi_physician_payments = self.env['account.payment'].search(where1)
        result = []
        for ap in single_physician_payments:
            result.append({
                'date': ap.date.strftime('%d/%m/%Y'),
                'id': ap.name,
                'name': ap.partner_id.name,
                'physician': ap.physician_id.name,
                'journal_name': ap.journal_id.name,
                'total': ap.amount,
            })
        for ap in multi_physician_payments:
            result.append({
                'date': ap.date.strftime('%d/%m/%Y'),
                'id': ap.name,
                'name': ap.partner_id.name,
                'physician': ap.physician_id.name,
                'journal_name': ap.journal_id.name,
                'total': ap.amount,
            })
        result = sorted(result, key=lambda x: x['physician'] or '')
        if not result:
            raise UserError(_("There is no data with selected options."))

        return result

    def _get_title(self, data):
        new_st_dt = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        new_end_dt = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        dt_str = new_st_dt.strftime('%d-%m-%Y ')
        end_dt_str = new_end_dt.strftime('%d-%m-%Y ')
        return "Allocation by Practitioner for the Period  %s to %s" % (
            dt_str, end_dt_str)

    @api.model
    def _get_report_values(self, docids, data=None):
        payment_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_account_reports.allocation_by_practitioner')
        return {
            'doc_ids': self.ids,
            'docs': self,
            'with_name': data['form_data']['with_name'],
            'get_title': self._get_title(data['form_data']),
            'doc_model': payment_report.model,
            'clients': data['form_data']['client_id'],
            'get_data_from_report': self._get_data_from_report(
                data['form_data']),

        }
