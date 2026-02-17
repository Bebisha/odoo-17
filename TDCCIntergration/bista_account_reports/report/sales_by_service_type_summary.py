# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from odoo import models, api, _
# from odoo.exceptions import Warning
import warnings

from odoo.exceptions import UserError


class AccountReportSaleServiceTypeSummary(models.AbstractModel):
    _name = 'report.bista_account_reports.sales_by_service_type_summary'
    _description = 'TDCC Account Reports for Sales by Service Type Summary'

    def _get_data_from_report(self, data):

        dt1 = data['start_date']
        dt2 = data['end_date']
        where = "where am.state not in ('cancel','draft') and \
            aml.service_type_id is not NULL and \
                    am.invoice_date >='" + \
            dt1 + "' and am.invoice_date <='" + dt2 + "'"
        if data.get('service_type_id'):
            where += " and aml.service_type_id = " + \
                str(data['service_type_id'])
        query = """select
                    x.treatment_name as service_name,
                    x.move_type as move_type,
                    sum(x.sales) as sales
                    --sum(x.receipts) as receipts,
                    --sum(x.balance) as balance
                from
                    (select
                        am.invoice_date as date,
                        rp.name as partner_name,
                        am.move_type as move_type,
                        tt.name as treatment_name,
                        aml.price_subtotal as sales
                        --am.amount_total_signed-am.amount_residual_signed as receipts,
                        --am.amount_residual_signed as balance
                    from
                        account_move am
                        left join account_move_line aml
                        on am.id=aml.move_id
                        left join res_partner rp on rp.id=am.partner_id
                        left join service_type tt
                        on tt.id=aml.service_type_id """ + """
                    """ + where + """
                    ) x
                group by
                    x.treatment_name,
                    x.move_type
                order by
                    x.treatment_name,
                    x.move_type """

        self._cr.execute(query)
        res = self._cr.dictfetchall()
        if not res:
            raise UserError(_("There is no data with selected options."))
        return res

    def _get_title(self, data):
        return "Sales by  Service Type from %s to %s" % (
            data.get('start_date'),
            data.get('end_date'))

    @api.model
    def _get_report_values(self, docids, data=None):
        payment_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_account_reports.sales_by_service_type_summary')
        return {
            'doc_ids': self.ids,
            'docs': self,
            'get_title': self._get_title(data['form_data']),
            'doc_model': payment_report.model,
            'clients': data['form_data']['client_id'],
            'service_type': data['form_data']['service_type'],
            'get_data_from_report': self._get_data_from_report(
                data['form_data']),

        }
