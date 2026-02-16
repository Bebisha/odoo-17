# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class InvoicePaymentLog(models.Model):
    _name = 'invoice.payment.log'
    _description = 'Invoice Payment Log'
    _rec_name = 'invoice_id'

    invoice_id = fields.Many2one('account.move', string="Invoice Ref.",
                                 required=True)
    payment_id = fields.Many2one('account.payment', string="Payment Ref.")
    amount = fields.Float(string="Amount", required=True)
    date = fields.Date(string="Date")
    move_line_id = fields.Many2one('account.move.line', string="Move Line Ref.")
