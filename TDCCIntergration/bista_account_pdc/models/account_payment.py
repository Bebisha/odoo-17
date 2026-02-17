# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class AccountRegisterPayment(models.TransientModel):
    _inherit = "account.payment.register"

    effective_date = fields.Date('Effective Date', copy=False, default=False)
    cheque_date = fields.Date('Cheque Date', copy=False, default=False)
    related_journal = fields.Many2one('account.journal',
                                      string='Related Journal')

    def get_payments_vals(self):
        res = super(AccountRegisterPayment, self).get_payments_vals()
        check_met = \
            self.env.ref('account_check_printing.account_payment_method_check')
        if self.payment_method_id == check_met or \
                self.payment_method_code == 'pdc':
            for rec in res:
                rec.update({
                    'cheque_date': self.cheque_date,
                    'related_journal': self.related_journal and
                                           self.related_journal.id or False
                })
        return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    effective_date = fields.Date('Effective Date', copy=False, default=False)
    related_journal = fields.Many2one('account.journal',
                                      string='Related Journal')
    pdc_reconciled = fields.Boolean(copy=False, string='Pdc Reconciled')
    pdc_manual_payment = fields.Boolean(compute='_compute_pdc_type',
                                        copy=False,
                                        string='Display PDC Payment Button')
    cheque_date = fields.Date('Cheque Date', copy=False, default=False)
    cheque_clear = fields.Boolean('Check cleared?')
    cheque_move_line_ids = fields.One2many('account.move.line', 'cheque_payment_id', readonly=True, copy=False)
    cheque_no_char = fields.Char(string='Check No', tracking=True)

    @api.constrains('cheque_date')
    def _check_past_cheque_date(self):
        for record in self:
            if record.cheque_date and record.payment_type == 'inbound' and record.cheque_date < date.today():
                raise ValidationError(_('Cheque Date can not be past date.'))

    @api.constrains('cheque_no_char')
    def check_cheque_number(self):
        for rec in self:
            if rec.cheque_no_char and not rec.cheque_no_char.isdigit():
                raise ValidationError("Cheque number can not contain Char \
                    value. Add only numeric value.")
    
    @api.onchange('cheque_no_char')
    def onchnage_cheque_no_char(self):
        for rec in self:
            if rec.cheque_no_char:
                rec.check_number = int(rec.cheque_no_char)
            else:
                rec.check_number = False

    # @api.multi
    def action_pdc(self):
        """
        This will open a pop up where you can update effective date.
        """
        for rec in self:
            view_id = self.env.ref(
                'bista_account_pdc.wiz_view_account_pdc_form')
            return {
                'name': 'Account pdc Payment ',
                'type': 'ir.actions.act_window',
                'view_id': view_id.id,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'wiz.pdc.payment',
                'target': 'new',
            }

    @api.depends()
    def _compute_pdc_type(self):
        """
        sets pdc payment button true when pdc_type in account settings is set
        manual.
        """
        account_pdc_type = self.company_id.pdc_type
        for payment in self:
            payment.pdc_manual_payment = False
            if not payment.pdc_reconciled:
                if account_pdc_type == 'manual':
                    payment.pdc_manual_payment = True

                   
    @api.model
    def account_pdc(self):
        """
            This is scheduler method, will search Payments which in which
            Payment method is PDC and effective date is equal to today than it
            will create PDC JE and reconcile PDC entries.
        """
        account_pdc_type = self.company_id.pdc_type == 'automatic'
        if account_pdc_type:
            rec = self.search([('cheque_date', '=',
                                str(datetime.today().date())),
                               ('pdc_reconciled', '=', False),
                               ('payment_method_code', '=', 'pdc')])
            rec.create_move()

    # @api.multi
    def post(self):
        """
            This method will check Payment method is PDC and effective date is
            less or equal to today than it will create PDC JE and reconcile PDC
            entries.
        """
        res = super(AccountPayment, self).action_post()
        for rec in self:
            if rec.payment_method_code == 'pdc':
                if rec.cheque_date and rec.cheque_date <= datetime.today().date():
                    return res

    # @api.multi
    def create_move(self):
        """
        This method will create JE for PDC and also reconcile PDC entries.
        """
        account_move_obj = self.env['account.move']
        account_move_line_obj = self.env['account.move.line']
        for rec in self:
            if rec.partner_type == 'customer':
                if rec.payment_type == 'outbound':
                     mv1_debit = 0.0
                     mv1_credit = rec.amount
                     mv2_debit = rec.amount
                     mv2_credit = 0.0
                elif rec.payment_type == 'inbound':
                    mv1_debit = rec.amount
                    mv1_credit = 0.0
                    mv2_debit = 0.0
                    mv2_credit = rec.amount
                else:
                    mv1_debit = rec.amount
                    mv1_credit = 0.0
                    mv2_debit = 0.0
                    mv2_credit = rec.amount

            if rec.partner_type == 'supplier':
                if rec.payment_type == 'outbound':
                    mv1_debit = 0.0
                    mv1_credit = rec.amount
                    mv2_debit = rec.amount
                    mv2_credit = 0.0
                elif rec.payment_type == 'inbound':
                    mv1_debit = rec.amount
                    mv1_credit = 0.0
                    mv2_debit = 0.0
                    mv2_credit = rec.amount
                else:
                    mv1_debit = 0.0
                    mv1_credit = rec.amount
                    mv2_debit = rec.amount
                    mv2_credit = 0.0
            move_line_1 = {
                'account_id':
                    rec.related_journal.default_debit_account_id.id,
                'name': '/',
                'debit': mv1_debit,
                'credit': mv1_credit,
                'company_id': rec.company_id.id,
                'date_maturity': rec.effective_date and rec.effective_date or
                                 rec.cheque_date,
                'cheque_payment_id': rec.id,
            }
            move_line_2 = {
                'account_id': rec.journal_id.default_credit_account_id.id,
                'name': rec.check_number,
                'credit': mv2_credit,
                'debit': mv2_debit,
                'company_id': rec.company_id.id,
                'date_maturity': rec.effective_date and rec.effective_date or
                                 rec.cheque_date,
                'cheque_payment_id': rec.id,
            }
            move = account_move_obj.create({
                'journal_id': rec.related_journal.id,
                'date': rec.effective_date and rec.effective_date or
                        rec.cheque_date,
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
                'ref': rec.check_number
            })
            move.post()
            rec.state = 'posted'
            # search move lines of PDC, to reconcile
            if (rec.partner_type == 'customer' and rec.payment_type == 'inbound') or (rec.partner_type == 'supplier' and rec.payment_type == 'inbound'):
                move_lines = account_move_line_obj.search([
                    ('move_id', '=', move.id),
                    ('credit', '!=', 0.0)])
                move_lines += account_move_line_obj.search([
                    ('payment_id', '=', rec.id),
                    ('debit', '!=', 0.0)])
            if (rec.partner_type == 'customer' and rec.payment_type == 'outbound') or (rec.partner_type == 'supplier' and rec.payment_type == 'outbound'):
                move_lines = account_move_line_obj.search([
                    ('move_id', '=', move.id),
                    ('debit', '!=', 0.0)])
                move_lines += account_move_line_obj.search([
                    ('payment_id', '=', rec.id),
                    ('credit', '!=', 0.0)])
            # reconcile move lines
            move_lines_filtered = move_lines.filtered(
                lambda aml: not aml.reconciled)
            move_lines_filtered.with_context(
                skip_full_reconcile_check='amount_currency_excluded'
            ).reconcile()
            # move_lines.force_full_reconcile()
            rec.pdc_reconciled = True

    # @api.multi
    def cheque_bounce(self):
        """
         This will raise warning if effective date is greater than current date
         else it will unlink move and set state as draft.
        """
        for payment_rec in self:
            if isinstance(payment_rec.cheque_date, datetime) and payment_rec.cheque_date.date() > datetime.today().date():

            # if payment_rec.cheque_date > datetime.today().date():
                raise ValidationError(_(
                    "Check can not bounced before Cheque date!"))
            payment_rec.with_context({'cheque_bounce': True}).cancel()
            payment_rec.state = 'draft'


    # @api.multi
    def cancel(self):
        # res = super(AccountPayment, self).cancel()
        for rec in self:
            for cheque_move in rec.cheque_move_line_ids.mapped('move_id'):
                cheque_move.line_ids.remove_move_reconcile()
                cheque_move.button_cancel()
                cheque_move.unlink()
            if rec.cheque_clear:
                rec.cheque_clear = False
        return

    # @api.multi
    def action_draft(self):
        for rec in self:
            rec.pdc_reconciled = False
            rec.cheque_clear = False
            rec.effective_date = False
        return super(AccountPayment, self).action_draft()

    # @api.multi
    def button_check_journal_entries(self):
        return {
            'name': 'Journal Items',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('cheque_payment_id', 'in', self.ids)],
        }


class MoveLine(models.Model):

    _inherit = 'account.move.line'

    cheque_payment_id = fields.Many2one('account.payment', string='Payment')
