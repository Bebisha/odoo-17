# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from odoo import models, api


class VatReport(models.AbstractModel):
    _name = 'report.bista_account_reports.vat_report_pdf'
    _description = 'TDCC Vat Report'

    # @api.multi
    # def get_with_trn_data(self, data):
    #     data = data
    #     return data

    # @api.multi
    # def get_without_trn_data(self, data):
    #     data = data
    #     return data

    # @api.multi
    # def get_customer_vat_data(self, data):
    #     data = data
    #     return data

    @api.model
    def _get_report_values(self, docids, data=None):
        vat_report = self.env['ir.actions.report']._get_report_from_name(
            'bista_account_reports.vat_report_pdf')
        return {
            'doc_ids': self.ids,
            'docs': self,
            'doc_model': vat_report.model,
            'get_with_trn_data': data['form_data'][0],
            'get_without_trn_data': data['form_data'][1],
            'get_customer_vat_data': data['form_data'][2]

        }
