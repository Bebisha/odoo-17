# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api


class AccountReportWizard(models.TransientModel):
    _name = 'account.report.wizard'
    _description = 'Account Report'

    start_date = fields.Date(string='Start Date',
                             default=fields.date.today())
    end_date = fields.Date(string='End Date',
                           default=fields.date.today())
    report_type = fields.Selection(
        [('receipt_by_payment_method', 'Receipt by payment Method'),
         ('sales_by_practitioner', 'Sales By Practitioner'),
         ('appoint_by_practitioner', 'Appointment By Practitioner'),
         ('allocation_by_practitioner', 'Allocation By Practitioner'),
         ('sales_by_service_type', 'Sales By Service Type'),
         ('receipt_by_payment_method_je', 'Receipt by payment Method(JE)')],
        default='receipt_by_payment_method',
        required=True)
    report_format = fields.Selection([('detail', 'Detail'),
                                      ('summary', 'Summary')],
                                     default='detail')
    client_id = fields.Many2one('res.partner',
                                string='Client',
                                )
    user_id = fields.Many2one('res.users', string='Physician')
    phy_id = fields.Many2one('res.partner',
                             string='Practitioner',
                             domain=[('is_physician', '=', True)])
    service_type_id = fields.Many2one('service.type',
                                      string='Service Type')
    service_type_ids = fields.Many2many('service.type',
                                        string='Service Types')
    code_id = fields.Many2one('physician.code', string='Code')
    with_name = fields.Boolean(string='With Physician Name')

    # @api.multi
    def print_report(self):
        self.ensure_one()
        [data] = self.read()
        form_data = {
            'client_id': self.client_id.id,
            'client': self.client_id.name,
            'user_id': self.user_id.id,
            'phy_id': self.phy_id.id,
            'service_type_ids': self.service_type_ids.ids,
            'service_type_id': self.service_type_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'report_type': self.report_type,
            'code_id': self.code_id.id,
            'service_type': self.service_type_id.name,
            'with_name': self.with_name
        }
        datas = {
            'ids': self._ids,
            'model': 'account.payment',
            'form': data,
            'form_data': form_data
        }
        if self.report_type == 'receipt_by_payment_method' and \
                self.report_format == 'detail':
            return self.env.ref(
                'bista_account_reports.report_by_paymentmethod'
            ).report_action(self, data=datas)

        elif self.report_type == 'receipt_by_payment_method' and \
                self.report_format == 'summary':
            return self.env.ref(
                'bista_account_reports.report_payment_method_summary'
            ).report_action(self, data=datas)

        elif self.report_type == 'receipt_by_payment_method_je':
            return self.env.ref(
                'bista_account_reports.report_payment_method_summary_je'
            ).report_action(self, data=datas)

        elif self.report_type == 'sales_by_practitioner' and \
                self.report_format == 'detail':
            return self.env.ref(
                'bista_account_reports.report_sales_by_practitioner_detail'
            ).report_action(self, data=datas)

        elif self.report_type == 'sales_by_practitioner' and \
                self.report_format == 'summary':
            return self.env.ref(
                'bista_account_reports.report_sales_by_practitioner_summary'
            ).report_action(self, data=datas)

        elif self.report_type == 'appoint_by_practitioner':
            return self.env.ref(
                'bista_account_reports.report_app_by_practitioner'
            ).report_action(self, data=datas)

        elif self.report_type == 'allocation_by_practitioner':
            return self.env.ref(
                'bista_account_reports.report_allocation_by_prac'
            ).report_action(self, data=datas)

        elif self.report_type == 'sales_by_service_type' and \
                self.report_format == 'detail':
            return self.env.ref(
                'bista_account_reports.report_sales_by_service_type'
            ).report_action(self, data=datas)

        elif self.report_type == 'sales_by_service_type' and \
                self.report_format == 'summary':
            return self.env.ref(
                'bista_account_reports.report_sales_by_service_type_summary'
            ).report_action(self, data=datas)
