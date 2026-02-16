# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from odoo import api, models, fields, _
import warnings


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    invoice_payment_line_ids = fields.One2many('invoice.payment.line',
                                               'invoice_id',
                                               string='Payment Lines')


    # @api.onchange('invoice_payment_term_id', 'invoice_date')
    # def _onchange_payment_term_date_invoice(self):
    #
    #     """ Inherit method to create journal entry from Invoice payment lines
    #         instead of payment term lines.  """
    #
    #     if self.invoice_payment_line_ids and self.move_type == 'out_invoice':
    #         date_invoice = self.invoice_date
    #         if not date_invoice:
    #             date_invoice = fields.Date.context_today(self)
    #         if self.invoice_payment_term_id:
    #             pterm = self.invoice_payment_term_id
    #             pterm_list = [(fields.Date.to_string(line.payment_date),
    #                            line.amount)
    #                           for line in self.invoice_payment_line_ids]
    #             self.invoice_date_due = max(line[0] for line in pterm_list)
    #         elif self.invoice_date_due and (date_invoice > self.invoice_date_due):
    #             self.invoice_date_due = date_invoice
    #     else:
    #         return super(AccountInvoice, self.with_context(my_inv_id=self.id)
    #                      )._onchange_payment_term_date_invoice()

    @api.onchange('invoice_payment_term_id', 'invoice_date')
    def _onchange_payment_term_date_invoice(self):
        """ Inherit method to create a journal entry from Invoice payment lines
            instead of payment term lines.  """

        if self.invoice_payment_line_ids and self.move_type == 'out_invoice':
            date_invoice = self.invoice_date
            if not date_invoice:
                date_invoice = fields.Date.context_today(self)
            if self.invoice_payment_term_id:
                pterm = self.invoice_payment_term_id
                pterm_list = [(fields.Date.to_string(line.payment_date),
                               line.amount)
                              for line in self.invoice_payment_line_ids]
                self.invoice_date_due = max(line[0] for line in pterm_list)
            elif self.invoice_date_due and (date_invoice > self.invoice_date_due):
                self.invoice_date_due = date_invoice
        # No need to call the super method here
