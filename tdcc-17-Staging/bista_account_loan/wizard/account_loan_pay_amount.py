# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountLoan(models.TransientModel):
    _name = 'account.loan.pay.amount'
    _description = 'Loan Pay Amount'

    @api.model
    def _get_default_ammount(self):
        context = dict(self._context)
        if context and context.get('active_id'):
            line_rec = self.env['account.loan.line'].browse(
                context.get('active_id'))
            if not line_rec:
                return False
            return line_rec.amount

    @api.model
    def _get_default_intrests(self):
        context = dict(self._context)
        if context and context.get('active_id'):
            line_rec = self.env['account.loan.line'].browse(
                context.get('active_id'))
            if not line_rec:
                return False
            return line_rec.interest_amount

    loan_id = fields.Many2one(
        'account.loan',
    )
    loan_line_id = fields.Many2one(
        'account.loan.line', String="Loan Line")
    currency_id = fields.Many2one(
        'res.currency',
        related='loan_id.currency_id',
        readonly=True
    )

    date = fields.Date(required=True, default=fields.Date.today())
    amount = fields.Monetary(
        currency_field='currency_id',
        string='Principal Amount', default=_get_default_ammount,
    )
    fees = fields.Monetary(
        currency_field='currency_id',
        string='Interests', default=_get_default_intrests)
    total_amount = fields.Monetary(
        currency_field='currency_id',
        string='Total', compute='compute_total_amount')

    @api.depends('amount', 'fees')
    def compute_total_amount(self):
        for rec in self:
            self.total_amount = self.amount + self.fees

    def new_line_vals(self, sequence):
        return {
            'loan_id': self.loan_id.id,
            'sequence': sequence,
            'payment_amount': self.amount + self.fees,
            'rate': 0,
            'interests_amount': self.fees,
            'date': self.date,
        }

    # @api.multi
    def run(self):

        self.loan_line_id.view_process_values()
        self.loan_line_id.state = 'paid'
