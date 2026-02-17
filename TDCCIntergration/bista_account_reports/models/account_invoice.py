# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    annual_invoice_date = fields.Date(
        string="Annual Invoice Registration Date")

    # @api.multi
    def action_annual_invoice(self):
        if not self.annual_invoice_date:
            raise UserError(_(
                'Please set Annual Invoice Registration Date on invoice'))
        return self.env.ref('bista_account_reports.'
                            'action_annual_invoice').report_action(self)

    def generate_account_ref(self):
        account_ref = ''
        if self.date_invoice:
            month = self.date_invoice.strftime("%b")
            day = self.date_invoice.strftime("%d")
            account_ref = 'TDCC/ACC/Inv/' + month + '-' + day
        return account_ref
