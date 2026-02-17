from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import  warnings
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT, float_round
import logging

_logger = logging.getLogger(__name__)

try:
    import numpy
except (ImportError, IOError) as err:
    _logger.error(err)


class AccountLoan(models.Model):
    _name = 'account.loan'
    _inherit = ['mail.thread']
    _description = 'Finance Lease'
    _order = 'name desc'

    @api.constrains('loan_amount', 'installment_number')
    def _check_loan_amount(self):
        """
        Validation for loan amount and installment number should not be 0
        :return:
        """
        if self.loan_amount <= 0.0:
            raise ValidationError(
                _("Finance Lease amount should be greater then 0"))
        if self.installment_number <= 0:
            raise ValidationError(
                _("Installment Number should be greater then 0"))

        # if self.rate <= 0:
        #     raise ValidationError(
        #         _("Please Enter Rate greater than 0"))

    @api.model
    def _get_sequence(self):
        seq = self.env['ir.sequence'].next_by_code('account.loan.sequence')
        return seq

    def _get_current_date(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.depends('line_ids')
    def compute_installment_payment(self):
        """
        compute
        - total paid installment amount
        - remaining installments total_amount
        :return:
        """
        for rec in self:
            total_paid_installment = 0.00
            for inst_line in rec.line_ids:
                if inst_line.state in ['paid', 'cancel']:
                    total_paid_installment += inst_line.amount
            rec.total_paid_installment_amount = total_paid_installment
            rec.remaining_installments_total_amount = abs(
                rec.loan_amount - total_paid_installment)

    # @api.constrains('loan_amount', 'calculate_amount')
    # def check_dates(self):
    #     '''
    #     This method is used to validate the start date and end date.
    #     '''
    #     if self.calculate_amount > self.loan_amount:
    #             raise ValidationError(_('Calculate amount cannot be \
    #              greater than loan amount!'))

    name = fields. \
        Char(string="Request Number", copy=False, default='New')
    partner_id = fields.Many2one('res.partner', 'Customer', copy=False)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id,
                                 string='Company',
                                 )
    loan_amount = fields.Float('Loan Amount')
    installment_number = fields.Integer('Number of Installments')
    state = fields.Selection([('draft', 'To Submit'),
                              ('finance_processing',
                               'Waiting For Finance Approval'),
                              ('approved', 'Confirm'),
                              ('rejected', 'Rejected'),
                              ('cancelled', 'Cancelled'),
                              ('done', 'Done')],
                             string='Status', readonly=True,
                             tracking=True,
                             help='When the Finance Lease is created the status is '
                                  '\'Draft\'.\n Then the request will be '
                                  'forwarded to approval.',
                             default='draft')
    line_ids = fields.One2many('account.loan.line', 'loan_id')
    repayment_method = fields.Selection([('payroll', 'Payroll'),
                                         ('cash_bank', 'Cash/Bank')],
                                        copy=False,
                                        string='RePayment Method')
    total_paid_installment_amount = fields.Float(
        compute='compute_installment_payment',
        string='Total Paid Installment')
    remaining_installments_total_amount = fields.Float(
        compute='compute_installment_payment',
        string='Total Remaining Installments')
    loan_journal_id = fields.Many2one('account.journal', string='Journal')
    debit_account_id = fields.Many2one('account.account',
                                       string='Principal Account')
    credit_account_id = fields.Many2one('account.account',
                                        string='Interest Account')
    loan_issuing_date = fields.Date(
        string='Installment Start From',
        copy=False)
    start_date = fields.Date(
        string='Installment Start Date',
        copy=False,
     default=_get_current_date)

    accounting_date = fields.Date(string='Accounting Date', copy=False)
    comments = fields.Text('Comments')
    reject_reason = fields.Text('Reject Reason')
    loan_approve_date = fields.Date(string='Approved Date')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    move_ids = fields.One2many(
        'account.move',
        copy=False,
        inverse_name='loan_id'
    )

    rate = fields.Float(
        digits=0,
        help='Currently applied rate',
        tracking=True,
    )
    rate_period = fields.Float(
        compute='_compute_rate_period', digits=(16, 7),
        help='Real rate that will be applied on each period',
    )

    loan_history_ids = fields.One2many(
        'account.loan.history',
        'loan_id',
     string='Loan History')

    @api.depends('rate')
    def _compute_rate_period(self):
        """
        Returns the real rate
        :param rate: Rate
        :param rate_type: Computation rate
        :param method_period: Number of months between payments
        :return:
        """
        for rec in self:
            rec.rate_period = (rec.rate / 12) / 100

    # @api.multi
    def view_account_moves(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_line_form')
        result = action.read()[0]
        result['domain'] = [('loan_id', '=', self.id)]
        return result

    # @api.multi
    def action_draft(self):
        """
        Method to set draft state
        """
        for rec in self:
            rec.state = 'draft'
        return True

    @api.model
    def create(self, vals):
        """
            :return: name sequence
        """

        if vals.get('name', 'New') == 'New':
            if 'company_id' in vals:
                vals[
                    'name'] = self.env[
                        'ir.sequence'].with_context(
                            force_company=vals[
                                'company_id']).next_by_code(
                    'account.loan.sequence') or _(
                        'New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'account.loan.sequence') or 'New'
        return super(AccountLoan, self).create(vals)

    # @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You cannot delete Finance Lease."))
        return super(AccountLoan, self).unlink()

    # @api.multi
    def _get_related_window_action_id(self, data_pool):
        """
        getting related window action for making email link
        :param data_pool:
        :return:
        """
        window_action_id = False
        window_action_ref = \
            'bista_account_loan.open_loan_request_for_finance_lease'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id

    # @api.multi
    def action_submit_for_finance_lease_approval(self):
        """
       method call from Button Submit for Finance Approval
       :return:
       """
        for rec in self:
            rec.state = 'finance_processing'
        return True
        # self.write({'state': 'finance_processing'})

    # @api.multi
    def check_installments(self):
        if not self.line_ids:
            self.calculate_loan_amount()

    # @api.multi
    def action_approved_loan(self):
        """
       method call from Button Submit for Approve
       :return:
       """
        self.check_installments()
        self.write({'state': 'approved',
                    'loan_approve_date': self._get_current_date()})

        message = ('''<ul class="o_mail_thread_message_tracking">
                      <li>Loan Approve Date Date: %s</li>
                      <li>Loan Number: %s </li>
                      <li>State: %s</li>
                      </ul>''') % (
            datetime.now().strftime(OE_DTFORMAT),
            self.name, self.state.title())
        self.accounting_date = self._get_current_date()
        self.message_post(body=message)
        self.action_move_create()
        self.env['account.loan.history'].create({'start_date': self.start_date,
                                                'loan_id': self.id, 'rate': self.rate})

    # @api.multi
    def action_submit_loan_reject(self):
        """
        this method will call for reject loan request
        this will open wizard for reject reason
        :return:
        """
        ctx = dict(self._context)
        form_view = self.env.ref(
            'bista_account_loan.account_loan_reject_form_view')
        return {
            'name': _('Reject Reason'),
            'res_model': 'loan.reject.reason',
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'
        }

    # @api.multi
    def action_submit_loan_cancelled(self):
        """
        This method will call when user press cancel loan request and loan
        request will be in cancelled state
        """
        self.write({'state': 'cancelled'})
        self.line_ids.write({'state': 'cancel'})

    # @api.multi
    def calculate_loan_amount(self):
        """
          method call from Button Calculate Loan Insallments
          :return:
          """
        loan_list = []
        for rec in self:

            loan_amount = rec.loan_amount
            installment_number = rec.installment_number
            if loan_amount and installment_number:
                amount = loan_amount / installment_number
                remaining_amount = loan_amount
                interest_amount = 0
                total_amount = 0.0
                payroll_run_date = self.start_date
                du_date = 0
                # create installment
                for duration in range(1, installment_number + 1):

                    amt = -(
                        numpy.pmt(
                            rec.rate_period, installment_number - duration + 1,
                           remaining_amount))
                    interest_amount = remaining_amount * rec.rate_period
                    remaining_amount = abs(
                        remaining_amount -
                        float_round(
                            amt -
                            interest_amount,
                            2))
                    du_date = duration
                    vals = {
                        'due_date': payroll_run_date + relativedelta(
                            months=du_date - 1),
                        'total_amount': amt,
                        'interest_amount': interest_amount,
                        'remaining_amount': remaining_amount,
                        'rate_month': rec.rate_period,
                        'state': 'draft',
                        'loan_id': rec.id,
                        'sr_number': duration,
                    }

                    total_amount += float_round(amount, 2)

                    loan_list.append((0, 0, vals))
                last_amount = loan_amount - total_amount
                # last installment adding for solve rounding issues
                if last_amount != 0:
                    loan_list[-1][2]['amount'] = \
                        loan_list[-1][2].get('total_amount') + last_amount
                # To remove duplicate lines
            for installment_rec in self.line_ids:
                loan_list.append((2, installment_rec.id))

            self.line_ids = loan_list

    # @api.multi
    def clear_installment_line(self):
        """
        this method will clear loan installments
        :return:
        """
        self.write(
            {'line_ids': [(2, self.line_ids.ids)]})

    # @api.multi
    def action_move_create(self):
        '''
        :return: Create First entry of total loan amount.
        '''
        move = self.env['account.move'].create({
            'journal_id':
                self.loan_journal_id.id if self.loan_journal_id else False,
            'company_id':
                self.env.user.company_id.id if self.env.user.company_id
                else False,
            'date': self.accounting_date,
            'ref': self.name,
            'name': '/',
        })
        if move:
            move_line_lst = self._prepare_move_lines(move)
            move.line_ids = move_line_lst
            move.loan_id = self.id
            move.post()

    def _prepare_move_lines(self, move):
        """
        :param move: Created move.
        :return: Create Approve loan JE's(First JE's).
        """
        move_lst = []
        if self.loan_journal_id and \
            (not self.loan_journal_id.default_debit_account_id
             or not self.loan_journal_id.default_credit_account_id):
            raise UserError(_("Selected journal have must be Default Credit and Debit account."))

        generic_dict = {
            'name': self.name,
            'company_id':
                self.env.user.company_id.id if self.env.user.company_id
                else False,
            'currency_id':
                self.env.user.company_id.currency_id.id
                if self.env.user.company_id and
                   self.env.user.company_id.currency_id else False,
            'date_maturity': self.loan_issuing_date,
            'journal_id':
                self.loan_journal_id.id if self.loan_journal_id else False,
            'date': self.accounting_date,
            'partner_id':
                self.partner_id.id,
            'quantity': 1,
            'move_id': move.id,
        }
        debit_entry_dict = {
            'account_id': self.loan_journal_id and
                          self.loan_journal_id.default_debit_account_id and
                          self.loan_journal_id.default_debit_account_id.id
                          or False,
            'debit': self.loan_amount,
        }
        credit_entry_dict = {
            'account_id': self.debit_account_id.id,
            'credit': self.loan_amount,
        }
        debit_entry_dict.update(generic_dict)
        credit_entry_dict.update(generic_dict)
        move_lst.append((0, 0, debit_entry_dict))
        move_lst.append((0, 0, credit_entry_dict))
        return move_lst

    # @api.multi
    def action_open_journal_entries(self):
        res = self.env['ir.actions.act_window'].\
            for_xml_id('account', 'action_move_journal_line')
        # DO NOT FORWARD-PORT
        res['domain'] = [('ref', 'in', self.mapped('name'))]
        res['context'] = {}
        return res

    def compute_posted_lines(self):
        """
        Recompute the amounts of not finished lines. Useful if rate is changed
        """
        amount = self.loan_amount
        for line in self.line_ids.sorted('sr_number'):
            if line.move_ids:
                amount = line.paid_amount
            else:
                line.interest_amount = line.remaining_amount * line.rate_month

                if line.sr_number == line.loan_id.installment_number:
                    line.total_amount = line.amount + line.interest_amount

                else:
                    line.total_amount = - numpy.pmt(
                        line.rate_month,
                        line.loan_id.installment_number - line.sr_number + 1,
                        line.remaining_amount)
                amount -= line.total_amount - line.interest_amount
