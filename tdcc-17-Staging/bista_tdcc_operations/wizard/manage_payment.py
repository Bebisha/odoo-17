from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero
from datetime import date


class ManageOutstandingPayment(models.TransientModel):
    _name = 'manage.outstanding.payment'
    _description = 'Manage Outstanding Payments'


    def default_get(self, fields):
        context = dict(self._context) or {}
        res = super(ManageOutstandingPayment, self).default_get(fields)
        if res is None:
            res = {}
        invoice_recs = self.env['account.move'].browse(
            context.get('active_ids', []))
        line_lst = []
        for invoice_rec in invoice_recs:
            res.update({'invoice_id': invoice_rec.id})
            partner_id = self.env['res.partner']._find_accounting_partner(
                invoice_rec.partner_id)
            # Collect account IDs from invoice line items
            account_ids = invoice_rec.invoice_line_ids.mapped('account_id.id')
            domain = [('account_id', 'in', account_ids),
                      ('partner_id', '=', partner_id.id),
                      ('reconciled', '=', False),
                      ('amount_residual', '!=', 0.0)]
            if invoice_rec.move_type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
            lines = self.env['account.move.line'].search(domain)
            if len(lines) != 0:
                for line in lines:
                    # get the outstanding residual value in invoice currency
                    if line.currency_id and line.currency_id == invoice_rec.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        amount_to_show = line.company_id.currency_id.with_context(
                            date=line.date).compute(abs(line.amount_residual),
                                                    invoice_rec.currency_id)
                    if float_is_zero(amount_to_show, precision_rounding=invoice_rec.currency_id.rounding):
                        continue
                    line_lst.append({
                        'move_line_id': line.id,
                        'payment_amount': abs(line.balance),
                        'currency_id':
                            line.currency_id and line.currency_id.id or invoice_rec.currency_id.id,
                        'remaining_amount': amount_to_show
                    })
        res.update(
            {'outstanding_payment_line_ids': [(0, 0, line_dict) for line_dict in line_lst]})
        return res

    invoice_id = fields.Many2one('account.move', 'Invoice')
    currency_id = fields.Many2one('res.currency',
                                  related='invoice_id.currency_id',
                                  string='Currency')
    partner_id = fields.Many2one('res.partner',
                                 related='invoice_id.partner_id',
                                 string='Customer')
    invoice_amount = fields.Monetary(string='Amount Due',
                                     related='invoice_id.amount_residual',
                                     help="Remaining amount due.")
    outstanding_payment_line_ids = fields.One2many(
        'manage.outstanding.payment.line',
        'outstanding_payment_id',
        'Outstanding Payment Lines')

    @api.constrains('outstanding_payment_line_ids')
    def _check_invoice_amount(self):
        for rec in self:
            added_amount = sum(
                line.amount for line in rec.outstanding_payment_line_ids)
            if added_amount > rec.invoice_amount:
                raise ValidationError(_('You cannot add more amount than \
                                         due amount of invoice!'))


    def manage_entries(self):
        line_to_reconcile = []
        payment_line = []
        line_to_reconcile = []
        update_move_line_dict = {}
        for rec in self:
            invoice_rec = rec.invoice_id
            for line in rec.outstanding_payment_line_ids:
                if line.amount:
                    credit_aml = line.move_line_id
                    # Multi Currency
                    if invoice_rec.currency_id != invoice_rec.company_id.currency_id:
                        old_amount_residual_currency = credit_aml[
                            'amount_residual_currency']
                        amount_residual = credit_aml['amount_residual']
                        new_amount_residual = invoice_rec.company_id.currency_id.with_context(
                            date=credit_aml.date).compute(line.amount, invoice_rec.currency_id)
                        credit_aml.write({
                            'amount_residual': -new_amount_residual,
                            'amount_residual_currency': -line.amount})
                        credit_aml.payment_id.write(
                            {'invoice_ids': [(4, invoice_rec.id, None)]})
                        invoice_rec.register_payment(credit_aml)
#                             'amount_residual_currency': old_amount_residual_currency + line.amount})
                    else:
                        if invoice_rec.move_type in ('out_invoice', 'in_refund'):
                            old_amount_residual = credit_aml['amount_residual']
                            credit_aml.write({
                                'amount_residual': -line.amount})
                            credit_aml.payment_id.write({'invoice_ids': [
                                (4, invoice_rec.id, None)]})
                            invoice_rec.register_payment(credit_aml)
                        else:
                            old_amount_residual = credit_aml['amount_residual']
                            credit_aml.write({'amount_residual': line.amount})
                            credit_aml.payment_id.write({'invoice_ids': [
                                (4, invoice_rec.id, None)]})
                            invoice_rec.register_payment(credit_aml)
                    invoice_rec.write({'payment_log_ids': [
                        (0, 0, {'invoice_id': invoice_rec.id,
                                'payment_id': credit_aml.payment_id.id,
                                'amount': line.amount,
                                'date': date.today()})]})
        return True


class ManageOutstandingPaymentLine(models.TransientModel):
    _name = 'manage.outstanding.payment.line'
    _description = 'Manage Outstanding Payments Lines'

    outstanding_payment_id = fields.Many2one('manage.outstanding.payment')
    move_line_id = fields.Many2one('account.move.line', 'Payment')
    payment_amount = fields.Monetary('Amount Paid')
    remaining_amount = fields.Monetary('Amount Remaining')
    currency_id = fields.Many2one('res.currency', 'Currency')
    amount = fields.Float('Amount')

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount > rec.remaining_amount:
                raise ValidationError(_('You cannot use more than \
                                         remaining amount!'))
