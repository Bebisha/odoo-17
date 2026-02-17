# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round
import logging

_logger = logging.getLogger(__name__)

try:
    import numpy
except (ImportError, IOError) as err:
    _logger.error(err)


class AccountLoanHistory(models.Model):
    _name = 'account.loan.history'
    _description = "Account Loan History"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    rate = fields.Float('Rate')
    loan_id = fields.Many2one('account.loan', 'Finance Lease', copy=False)

    @api.constrains('start_date')
    def check_start_date(self):
        if self.start_date < self.loan_id.start_date:
            raise ValidationError(
                "You cannot Enter Start Date Before Installment Start Date")

    # @api.multi
    def create_history(self):
        for rec in self:
            all_history = self.search(
                [('loan_id', '=', self.loan_id.id)], order='id desc', limit=2)
            if len(all_history) == 2:
                all_history[1].end_date = self.start_date
            rec.loan_id.rate = self.rate
            remaining_amt = rec.loan_id.loan_amount
            lst = rec.loan_id.line_ids
            for line in rec.loan_id.line_ids:
                if not line.state == 'paid':
                    if self.start_date <= line.due_date:
                        if lst and len(lst) > line.sr_number - 2 and lst[line.sr_number - 2]:
                            remaining_amt = float_round(
                                lst[line.sr_number - 2].remaining_amount,
                                2)

                        line.rate_month = (self.rate / 12) / 100
                        line.total_amount = -(
                            numpy.pmt(line.rate_month,
                                      rec.loan_id.installment_number -
                                      line.sr_number + 1,
                                      remaining_amt)) or 0.0  # rec.loan_id.installment_number - line.sr_number + 1
                        line.interest_amount = (
                            remaining_amt * line.rate_month)
                        line.remaining_amount = remaining_amt - \
                            float_round(
                                line.total_amount -
                                line.interest_amount,
                                2)
