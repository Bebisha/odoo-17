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


class SponsorPaymentReport(models.AbstractModel):
    _name = 'report.bista_tdcc_hibah.report_sponsor_payment'
    _description = 'Sponsor Payments Reports'

    def _get_sponsor_data_from_report(self, data):
        partner_id = self.env['res.partner'].browse(
            int(data.get('partner_id')))

        where_clause = """WHERE inv.sponsor_id=%s AND aml.account_id = %s""" \
            % (partner_id.id, partner_id.account_sponsor_id.id)

        if not partner_id.account_sponsor_id:
            raise UserError(_('First configure sponsor account'))
        if data.get('from_date', False):
            where_clause += """
                        AND (inv.date AT TIME ZONE '%s') ::
                        date >= '%s'
                    """ % (self.env.user.tz or 'UTC',
                           str(data.get('from_date')))
        if data.get('to_date', False):
            where_clause += """
                        AND (inv.date AT TIME ZONE '%s') ::
                        date <= '%s'
                    """ % (self.env.user.tz or 'UTC', str(data.get('to_date')))
        query = """
            SELECT
                cust.name as student,
                inv.date_invoice as invoice_date,
                inv.date_due as duedate,
                inv.number as number,
                inv.origin as SouceDoc,
                inv.state as status,
                rc.name as currency,
                partner.name as responsible,
                aml.debit as amount
            FROM account_invoice inv
            LEFT JOIN account_move_line aml ON
                aml.move_id = inv.move_id
            LEFT JOIN res_partner cust ON
                inv.partner_id = cust.id
            LEFT JOIN res_partner sponsor ON
                inv.sponsor_id = sponsor.id
            LEFT JOIN res_currency rc ON
                inv.currency_id = rc.id
            LEFT JOIN res_users ru ON
                inv.user_id = ru.id
            LEFT JOIN res_partner partner ON
                ru.partner_id = partner.id
        """ + where_clause

        self._cr.execute(query)
        res = self._cr.dictfetchall()
        if not res:
            raise UserError(_('There is not data to print for this Sponsor.'))
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        sponsor_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_tdcc_hibah.report_sponsor_payment')
        partner_id = self.env['res.partner'].browse(
            data.get('form_data').get('partner_id'))
        return {
            'doc_ids': partner_id.ids,
            'docs': partner_id,
            'doc_model': sponsor_report.model,
            'from_date': data.get('form_data').get('from_date'),
            'to_date': data.get('form_data').get('to_date'),
            'get_sponsor_data_from_report': self._get_sponsor_data_from_report(
                data.get('form_data')),
        }
