# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from odoo import fields, models, api


class InvoicePaymentLine(models.Model):
    _name = 'invoice.payment.line'
    _description = 'Payment term lines for invoices'

    amount = fields.Float(string='Amount')
    payment_date = fields.Date(string='Payment Date')
    invoice_id = fields.Many2one('account.move', string='Invoice')
