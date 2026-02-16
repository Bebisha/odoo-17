# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    # @api.multi
    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).button_cancel()
        commison_obj = self.env['sale.commission'].sudo()
        for invoice in self:
            if invoice.move_type in ['out_invoice', 'out_refund'] and \
                    invoice.user_id and invoice.date_invoice:
                commission_id = commison_obj.search_and_create(
                    invoice.date_invoice, invoice.user_id)
                if commission_id:
                    commission_id.commission_line_ids.filtered(
                        lambda line: line.invoice_id.id == invoice.id).unlink()
        return res

    # @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        commission_obj = self.env['sale.commission'].sudo()
        for inv in self:
            if inv.move_type in ['out_invoice', 'out_refund'] and inv.user_id:
                commission_obj.search_and_create(inv.date_invoice, inv.user_id)
        return res

    # @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        self.ensure_one()
        residual = self.residual
        credit_aml = self.env['account.move.line'].browse(credit_aml_id)
        payment_amount = abs(credit_aml.amount_residual or
                             credit_aml.amount_residual_currency)

        if payment_amount > residual:
            payment_amount = residual
        res = super(AccountInvoice, self).assign_outstanding_credit(
            credit_aml_id)

        if credit_aml.payment_id and self.user_id \
            and self.move_type in ['out_invoice', 'out_refund']:
            credit_aml.payment_id.with_context(
                advance_payment=True).post_commission_line(self, self.user_id,
                                                           payment_amount)
        return res
