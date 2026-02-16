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


class AccountPaymentReportSale(models.AbstractModel):
    _name = 'report.bista_account_reports.sales_by_prititioner_detail'
    _description = 'TDCC Account Reports for Sales'

    def _get_data_from_report(self, data):
        users_env = self.env['res.users']
        dt1 = data['start_date']
        dt2 = data['end_date']
        where = "where am.move_type in ('out_invoice', 'out_refund') and \
                am.state not in ('draft', 'cancel') and \
                     am.invoice_user_id is not NULL and \
                     am.invoice_date::date >= '" + dt1 + \
                "' and am.invoice_date::date <= '" + dt2 + "'"
        if data['phy_id']:
            user = users_env.search([('partner_id', '=', data['phy_id'])],
                                    limit=1)
            if user:
                where += " and am.invoice_user_id = " + str(user.id)
            else:
                raise UserError(_('There is no User linked to this physician'))

        query = """SELECT DISTINCT ON (am.id) 
                        TO_CHAR(am.invoice_date::DATE, 'DD/MM/YYYY') AS date,
                        am.name AS id,
                        st.name AS service,
                        par.name AS physician,
                        client.name AS client_name,
                        company.name AS clinic,
                        am.amount_total_signed AS total,  
                        am.move_type AS move_type,
                        am.amount_total_signed AS receipt, 
                        CASE 
                            WHEN am.move_type = 'out_invoice' THEN am.amount_residual_signed
                            ELSE 0
                        END AS balance
                    FROM 
                        account_move am
                    LEFT JOIN 
                        account_move_line aml ON aml.move_id = am.id
                    LEFT JOIN 
                        service_type st ON aml.service_type_id = st.id
                    LEFT JOIN 
                        res_partner client ON am.partner_id = client.id
                    LEFT JOIN 
                        res_users res ON res.id = am.invoice_user_id
                    LEFT JOIN 
                        res_partner par ON par.id = res.partner_id
                    LEFT JOIN 
                        res_company company ON am.company_id = company.id
                    """ + where + """ 
                    ORDER BY am.id, am.invoice_date
                    """
        self._cr.execute(query)
        res = self._cr.dictfetchall()

        if not res:
            raise UserError(_("There is no data with selected options."))
        query1 = """select sum(j.due) as balance from(
        select sum(distinct i.balance) as due from (%s)  as i
        where i.balance > 0
        group by i.id) as j
        """ % query
        self._cr.execute(query1)
        res1 = self._cr.dictfetchone()
        balance = res1.get('balance') or 0
        print("ressssssssssssssssssss", res)
        print("balance", balance)
        return {'res': res, 'balance': balance}

    def _get_title(self, data):
        new_st_dt = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        new_end_dt = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        dt_str = new_st_dt.strftime('%d-%m-%Y ')
        end_dt_str = new_end_dt.strftime('%d-%m-%Y ')
        return "Sales by Practitioner for the period \
                 %s to %s" % (dt_str, end_dt_str)

    @api.model
    def _get_report_values(self, docids, data=None):
        payment_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_account_reports.sales_by_prititioner_detail')
        return {
            'doc_ids': self.ids,
            'docs': self,
            'get_title': self._get_title(data['form_data']),
            'doc_model': payment_report.model,
            'clients': data['form_data']['client_id'],
            'get_data_from_report': self._get_data_from_report(
                data['form_data']),

        }
