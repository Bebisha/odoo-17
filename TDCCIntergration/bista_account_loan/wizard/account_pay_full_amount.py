# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.tools import float_round


class LeasePayFullAmount(models.TransientModel):
    _name = 'lease.pay.full.amount'
    _description = 'Lease Pay Full Amount'

    @api.model
    def _get_default_pending_amount(self):
        context = dict(self._context)
        if context and context.get('active_id'):
            loan_rec = self.env['account.loan'].browse(
                context.get('active_id'))
            if not loan_rec:
                return False
            return loan_rec.remaining_installments_total_amount

    @api.model
    def _default_journal_id(self):
        loan_id = self._context.get('default_loan_id')
        if loan_id:
            return self.env['account.loan'].browse(loan_id).loan_journal_id.id

    loan_id = fields.Many2one(
        'account.loan',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='loan_id.currency_id',
        readonly=True
    )

    date = fields.Date(required=True, default=fields.Date.today())
    amount = fields.Monetary(
        currency_field='currency_id',
        string='Remaning Principal', default=_get_default_pending_amount
    )
    fees = fields.Monetary(
        currency_field='currency_id',
        string='Interest(In Amount)')
    total_amount = fields.Monetary(
        currency_field='currency_id',
        string='Total Payable Amount', compute='compute_total_amount')

    journal_id = fields.Many2one(
        'account.journal',
        required=True,
        default=_default_journal_id
    )

    @api.depends('amount', 'fees')
    def compute_total_amount(self):
        for rec in self:
            self.total_amount = self.amount + self.fees

    # @api.multi
    def pay_full_amount(self):
        res = []
        vals = {
            'loan_id': self.loan_id.id,
            'date': self.date,
            'ref': self.loan_id.name,
            'journal_id': self.journal_id.id,
            'line_ids': [(0, 0, vals) for vals in self.pay_full_amount_line()]}

        move = self.env['account.move'].create(vals)

        move.post()
        res.append(move.id)
        self.loan_id.state = 'done'
        # self.loan_id.remaining_installments_total_amount = 0.0
        for line in self.loan_id.line_ids:
            if line.state != 'paid':
                line.state = 'cancel'

    def pay_full_amount_line(self):
        vals = []
        partner = self.loan_id.partner_id.with_context(
            force_company=self.loan_id.company_id.id)
        vals.append({
            'account_id': self.loan_id.debit_account_id.id,
            'partner_id': partner.id,
            'debit': self.total_amount,
            'credit': 0,
        })
        vals.append({
            'account_id': self.loan_id.credit_account_id.id,
            'debit': 0,
            'credit': self.fees,
        })
        vals.append({
            'account_id':
                self.loan_id.loan_journal_id.default_credit_account_id and self.loan_id.loan_journal_id.default_credit_account_id.id,
            'debit': 0,
            'credit': float_round(self.amount, 2),
        })

        return vals
