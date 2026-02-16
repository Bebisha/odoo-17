# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, _
# from odoo.exceptions import Warning
import warnings
from datetime import datetime

from odoo.exceptions import UserError


class AccountPaymentReportJE(models.AbstractModel):
    _name = 'report.bista_account_reports.reportbypaymentmethodsummaryje'
    _description = 'TDCC Account Reports'

    def _get_data_from_report(self, data):
        dt1 = data.get('start_date')
        dt2 = data.get('end_date')
        where = " aj.type in ('cash', 'bank') " \
                " and aml.account_id = aj.default_account_id" \
                " and aml.parent_state = 'posted'" \
                " and am.date::date >= '" + dt1 + \
                "' and am.date::date <= '" + dt2 + "'"
        if data.get('client_id'):
                where += " and aml.partner_id = " + str(data.get('client_id'))
        query = """select
                        --am.name,
                        --am.date,
                        --partner.name,
                        sum(aml.debit)-sum(aml.credit) as amount,
                        aj.name as payment_method
                    from
                        account_move_line aml
                        left join account_journal aj
                        on aml.journal_id=aj.id
                        left join account_move am
                        on aml.move_id=am.id
                        --left join res_partner partner
                        --on aml.partner_id=partner.id
                        --left join account_account acc
                        --on aml.account_id=acc.id
                        --left join account_account_type atype
                        --on acc.user_type_id=atype.id
                    where
                        """ + where + """
                    Group By
                        aj.id
                        --am.id,
                        --partner.id
        """
        self._cr.execute(query)
        res = self._cr.dictfetchall()

        if not res:
            raise UserError(_("There is no data with selected options."))
        return res

    def _get_title(self, data):
        new_st_dt = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        new_end_dt = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        dt_str = new_st_dt.strftime('%d-%m-%Y ')
        end_dt_str = new_end_dt.strftime('%d-%m-%Y ')
        if data.get('client'):
            return "Receipts for %s from %s to %s" % (data.get('client'), dt_str, end_dt_str)
        else:
            return "Receipts from %s to %s" % (dt_str, end_dt_str)


    @api.model
    def _get_report_values(self, docids, data=None):
        payment_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_account_reports.report_payment_method_summary_je')
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