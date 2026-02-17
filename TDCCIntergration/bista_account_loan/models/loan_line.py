from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import warnings
from odoo.tools import float_round
import math
import logging
import numpy

_logger = logging.getLogger(__name__)

# try:
#     import numpy
# except (ImportError, IOError) as err:
#     _logger.error(err)


class AccountLoanLine(models.Model):
    _name = 'account.loan.line'
    _description = 'Loan Installment'
    _inherit = ['mail.thread']
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner',
                                 related='loan_id.partner_id',
                                 string='Customer', store=True)
    due_date = fields.Date(string='Due Date')
    amount = fields.Float('Principal', compute='_compute_total_amount')
    interest_amount = fields.Float('Interest')
    total_amount = fields.Float('Installment')
    remarks = fields.Text(string='Remarks')
    loan_id = fields.Many2one('account.loan', string='Loan Request')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('reject', 'Reject'),
        ('lock', 'Rescheduled'), ('cancel', 'Cancelled'), ('paid', 'Paid')],
        string='Status',
        default='draft', tracking=True)
    paid_amount = fields.Float(string='Total Paid Amount')
    paid_date = fields.Date(string='Paid Date', tracking=True)
    residual_amount = fields.Float(string='Residual Amount')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    prev_due_date = fields.Date(string='Previous Date')
    sr_number = fields.Integer(string='Sequence')
    remaining_amount = fields.Float(string='Remaining Amount')
    rate_month = fields.Float(string='Rate', digits=(16, 7))
    hide_payment_btn = fields.Boolean(
        string='Hide Payment Amount',
        compute='compute_invisible_payment_amount')
    rate = fields.Float(string='Main Rate', compute='_calculate_main_rate')
    move_ids = fields.One2many(
        'account.move',
        inverse_name='loan_line_id',
    )

    # @api.multi
    def _calculate_main_rate(self):
        for rec in self:
            rec.rate = rec.rate_month * 12 * 100

    # @api.multi
    def _compute_total_amount(self):
        for rec in self:
            if rec.total_amount:
                rec.amount = abs(rec.total_amount - rec.interest_amount)

    # @api.multi
    def button_reschedule(self):
        """
        this method will reschedule installments
        :return:
        """

        if self.loan_id:
            self.write({'state': 'lock'})

    # @api.multi
    def button_reject(self):
        """
        this method will reject reschedule req and
        apply due date which was previously due date
        :return:
        """
        if self.prev_due_date:
            self.due_date = self.prev_due_date
            self.state = 'reject'

    # @api.multi
    def ask_for_reschedule(self):
        """
        this method will move record in asked for reschedule
        :return: False
        """
        if self.loan_id.state == 'approved':
            ctx = dict(self._context)
            ctx.update({'loan_installment': self.id})
            form_view = self.env.ref(
                'bista_account_loan.loan_reschedule_installment')

            return {
                'name': _('Reschedule'),
                'res_model': 'reschedule.installment.wizard',
                'views': [(form_view.id, 'form'), ],
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }
            # self.write({'state': 'lock'})
        else:
            raise UserError(_("You cannot reschedule untill loan approved."))

    # @api.multi
    def check_move_amount(self):
        """
        Changes the amounts of the annuity once the move is posted
        :return:
        """
        self.ensure_one()

        interest_moves = self.move_ids.mapped('line_ids').filtered(
            lambda r: r.account_id == self.loan_id.credit_account_id
        )
        principal_moves = self.move_ids.mapped('line_ids').filtered(
            lambda r: r.account_id == self.loan_id.debit_account_id
        )
        self.interest_amount = (
            sum(interest_moves.mapped('credit')) -
                sum(interest_moves.mapped('debit'))
        )

        self.total_amount = (
            sum(principal_moves.mapped('debit')))

    def move_vals(self):
        return {
            'loan_line_id': self.id,
            'loan_id': self.loan_id.id,
            'date': self.due_date,
            'ref': self.loan_id.name,
            'journal_id': self.loan_id.loan_journal_id.id,
            'line_ids': [(0, 0, vals) for vals in self.move_line_vals()]
        }

    def move_line_vals(self):
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
            'credit': self.interest_amount,
        })
        vals.append({
            'account_id':
                self.loan_id.loan_journal_id.default_debit_account_id.id,
            'debit': 0,
            'credit': self.total_amount - self.interest_amount,
        })

        return vals

    # @api.multi
    def view_process_values(self):
        """Computes the annuity and returns the result"""
        res = []
        for record in self:
            if not record.move_ids:
                if record.loan_id.line_ids.filtered(
                        lambda
                                r: r.due_date < record.due_date and not r.move_ids
                ):
                    raise UserError(
                        _("Some Installement Payment isn't Paid yet"))
                move = self.env['account.move'].create(record.move_vals())

                move.post()
                res.append(move.id)

        action = self.env.ref('account.action_move_line_form')
        result = action.read()[0]
        result['context'] = {
            'default_loan_line_id': self.id,
            'default_loan_id': self.loan_id.id
        }
        result['domain'] = [('loan_line_id', '=', self.id)]
        if len(self.move_ids) == 1:
            res = self.env.ref('account.move.form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.move_ids.id

        return result

    @api.depends('state', 'loan_id.state', 'total_amount')
    # @api.multi
    def compute_invisible_payment_amount(self):
        for rec in self:
            flag = False
            if rec.state == 'draft' and float_round(rec.total_amount, 2) > 0.0 and rec.loan_id.state == 'approved':
                flag = True
            else:
                flag = False
            rec.hide_payment_btn = flag
