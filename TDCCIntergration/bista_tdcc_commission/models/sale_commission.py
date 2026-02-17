# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class SaleCommission(models.Model):
    _name = 'sale.commission'
    _inherit = ['mail.thread']
    _description = "Sales Commission"
    _order = 'id desc'

    def _compute_amount(self):
        for comm in self:
            if comm.start_date and comm.end_date:
                sales_amount = commission_by_sales = 0.00
                user_id = self.env['res.users'].search(
                    [('partner_id', '=', comm.partner_id.id)])
                sales_limit = user_id.sales_limit

                # calculate Sales Amount
                invoice_domain = [('date_invoice', '>=', str(comm.start_date)),
                                  ('date_invoice', '<=', str(comm.end_date)),
                                  ('move_type', '=', 'out_invoice'),
                                  ('state', 'not in', ('draft', 'cancel')),
                                  ('user_id', '=', user_id.id)]
                invoice_ids = self.env[
                    'account.move'].search(invoice_domain)
                sales_amount = sum(invoice.amount_untaxed
                                   for invoice in invoice_ids)
                if sales_amount > sales_limit:
                    commission_by_sales = (
                        (sales_amount - sales_limit) *
                        user_id.commission_percentage) / 100
                    comm.commission_by_sales = commission_by_sales

                comm.update({'sales_amount': sales_amount,
                             'commission_by_sales': commission_by_sales,
                             'receipt_amount': sum(
                                 line.payment_amount for line in
                                 comm.commission_line_ids),
                             'commission_by_receipt': sum(
                                 x.commission_amount for x in
                                 comm.commission_line_ids)})

    name = fields.Char(string="Name", required=True, copy=False, default='/')
    partner_id = fields.Many2one('res.partner', required=True, copy=False)
    start_date = fields.Date(string="From Date", required=True)
    end_date = fields.Date(string="To Date", required=True)
    clinic_id = fields.Many2one('res.company', 'Company',
                                default=lambda self:
                                self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency',
                                  related='clinic_id.currency_id',
                                  string='Currency')
    state = fields.Selection([('draft', 'Draft'),
                              ('expense_booked', 'Expense Booked'),
                              ('paid', 'Paid'), ('cancel', 'cancelled')],
                             string='Status', index=True,
                             readonly=True, default='draft',
                             tracking=True, copy=False)
    commission_line_ids = fields.One2many('sale.commission.line',
                                          'commission_id',
                                          string='Commission Lines',
                                          readonly=True)
    sales_limit = fields.Float(string="Sales Limit")
    sales_amount = fields.Float(string="Total Sales Amount",
                                compute='_compute_amount', store=True)
    receipt_amount = fields.Float(string="Total Receipt Amount",
                                  compute='_compute_amount', store=True)
    commission_by_sales = fields.Float(string="Commission By Sales",
                                       compute='_compute_amount', store=True)
    commission_by_receipt = fields.Float(string="Commission By Receipt",
                                         compute='_compute_amount', store=True)
    commission_cut_off_date = fields.Date(string="Cut off date")

    _sql_constraints = [
        ('commission_uniq', 'unique(partner_id, start_date, end_date)',
         'Commission is already created for this salesperson!'),
    ]

    @api.model
    def create(self, vals):
        # Sales Commission sequence
        vals['name'] = self.env['ir.sequence'].next_by_code('sale.commission')
        return super(
            SaleCommission, self.with_context(
                tracking_disable=False)).create(vals)

    def action_create_move_line(self, move_id):
        comm_due_acc_id = self.partner_id.property_account_payable_id
        currency_id = self.env.user.company_id.currency_id

        # Assuming salesperson_id and partner_id are Many2one fields on sale.commission
        comm_exp_acc_id = self.partner_id.property_account_receivable_id

        credit_aml_dict = {
            'journal_id': move_id.journal_id.id,
            'currency_id': currency_id.id,
            'name': _('Commission for %s ') % self.partner_id.name,
            'debit': 0.00,
            'credit': self.commission_by_sales,
            'account_id': comm_due_acc_id.id,
        }

        debit_aml_dict = {
            'journal_id': move_id.journal_id.id,
            'currency_id': currency_id.id,
            'name': _('Commission for %s ') % self.partner_id.name,
            'partner_id': self.partner_id.id,
            'debit': self.commission_by_sales,
            'credit': 0.00,
            'account_id': comm_exp_acc_id.id,
        }

        move_id.write({'line_ids': [(0, 0, credit_aml_dict), (0, 0, debit_aml_dict)]})
        return True

    def action_create_move(self):
        context = dict(self._context)
        vals = {'date': fields.date.today(),
                'company_id': self.clinic_id.id}
        if context.get('from_line'):
            journal_id = self.env['account.journal'].search([
                ('type', '=', 'bank')], limit=1)
            if not journal_id:
                raise UserError(_('Bank Journal not found'))
            ref = self.name + '-' + context.get('source')
            vals.update({'ref': ref,
                         'journal_id': journal_id.id})
        else:
            journal_id = self.env['ir.config_parameter'].sudo().get_param(
                'bista_tdcc_commission.commission_journal_id')
            vals.update({'ref': self.name or '',
                         'journal_id': int(journal_id)})

        move_id = self.env['account.move'].create(vals)
        return move_id

    # @api.multi
    def post_sale_commissions(self):
        for commission in self.filtered(
                lambda com: com.commission_by_sales > 0):
            move_id = commission.action_create_move()
            commission.action_create_move_line(move_id)
            move_id.action_post()
            commission.update({'state': 'expense_booked'})
        return True

    @api.model
    def _cron_post_sale_commissions(self):
        start_date = datetime.today().replace(day=1).date()
        domain = [('state', '=', 'draft'),
                  ('end_date', '<', start_date)]
        commission_ids = self.sudo().search(domain, order='id asc')
        commission_ids.post_sale_commissions()
        return True

    @api.model
    def _cron_post_receipt_commissions(self):
        prev_date = datetime.strftime(datetime.now() - timedelta(1),
                                      '%Y-%m-%d')
        domain = [('state', '=', 'draft'),
                  ('commission_id.state', '=', 'expense_booked'),
                  ('commission_id.commission_cut_off_date', '<=', prev_date),
                  ('commission_amount', '>', 0.00)]
        comm_line_obj = self.env['sale.commission.line']
        commission_line_ids = comm_line_obj.search(domain, order='id asc')
        commission_data = {}
        receipt_comm_obj = self.env['receipt.commission']
        start_date = datetime.today().replace(day=1).date()
        end_date = datetime.today().date() + relativedelta(day=31)
        amount = 0.00
        for line in commission_line_ids.filtered(
            lambda line: line.commission_date <=
                line.commission_id.commission_cut_off_date):
            partner = line.commission_id.partner_id
            if partner.id not in commission_data.keys():
                commission_data.update(
                    {partner.id: line.commission_amount or 0.0})
            else:
                commission_data.update({partner.id: commission_data.get(
                    partner.id, 0.0) + line.commission_amount})
        start_date = start_date + relativedelta(months=-1)
        end_date = end_date + relativedelta(months=-1, day=31)
        for partner, amount in commission_data.items():
            receipt_comm_id = receipt_comm_obj.search([
                ('partner_id', '=', partner),
                ('date', '>=', start_date),
                ('date', '<=', end_date)])
            if not receipt_comm_id:
                vals = {'partner_id': partner,
                        'date': fields.date.today(),
                        'start_date': start_date,
                        'end_date': end_date,
                        'amount': amount}
                receipt_comm_id = receipt_comm_obj.create(vals)
                cline_ids = commission_line_ids.filtered(
                    lambda l: l.partner_id.id == partner and
                              l.commission_date <=
                              l.commission_id.commission_cut_off_date)
                cline_ids.write(
                    {'receipt_commission_id': receipt_comm_id.id})
                journal_id = self.env['ir.config_parameter'].sudo().get_param(
                    'bista_tdcc_commission.commission_journal_id')
                # commission payable account
                acc_id = receipt_comm_id.partner_id.property_account_payable_id
                comm_due_acc_id = self.env.ref(
                    'l10n_tdcc_coa.1_tdcc_account_comdue')
                currency_id = self.env.user.company_id.currency_id
                date_start = str(receipt_comm_id.start_date)
                date_end = str(receipt_comm_id.end_date)
                vals = {'ref': 'Commission :' + date_start + ' - ' + date_end,
                        'journal_id': int(journal_id)}
                credit_aml_dict = {'name': _('Commission for %s ')
                                   % receipt_comm_id.partner_id.name,
                                   'debit': 0.00,
                                   'partner_id': receipt_comm_id.partner_id.id,
                                   'journal_id': int(journal_id),
                                   'currency_id': currency_id.id,
                                   'credit': receipt_comm_id.amount,
                                   'account_id': acc_id.id}
                debit_aml_dict = {'name': _('Commission for %s ')
                                  % receipt_comm_id.partner_id.name,
                                  'journal_id': int(journal_id),
                                  'currency_id': currency_id.id,
                                  'debit': receipt_comm_id.amount,
                                  'credit': 0.00,
                                  'account_id': comm_due_acc_id.id}

                vals.update({'line_ids': [(0, 0, credit_aml_dict),
                                          (0, 0, debit_aml_dict)]})
                move_id = self.env['account.move'].create(vals)
                move_id.action_post()
                line_ids = comm_line_obj.search([
                    ('receipt_commission_id', '=', receipt_comm_id.id)])
                line_ids.update_line_state()
        return True

    # @api.multi
    def search_and_create(self, date_invoice, salesperson_id):
        if salesperson_id and salesperson_id.allow_commission:
            # check configuration
            journal_id = self.env['ir.config_parameter'].sudo().get_param(
                'bista_tdcc_commission.commission_journal_id')
            if not journal_id:
                raise UserError(_(
                    "You should configure the 'Commission Journal'"
                    "in the accounting settings,"
                    "to manage accounting entries related"
                    "to sales commission."))
            start_date = date_invoice.replace(day=1)
            end_date = date_invoice + relativedelta(day=31)
            domain = [('state', '!=', 'paid'),
                      ('partner_id', '=', salesperson_id.partner_id.id),
                      ('start_date', '<=', str(start_date)),
                      ('end_date', '>=', str(end_date))]
            commission = self.sudo().search(domain, limit=1)
            user_cutoff_date = salesperson_id.cut_off_date
            cutoff_dt = start_date + relativedelta(months=1)
            cutoff_month = cutoff_dt.strftime('%m')
            cutoff_date = user_cutoff_date.strftime('%d')
            if int(cutoff_month) == 2 and int(cutoff_date) == 30:
                cutoff_date = 28
            commission_cut_off_date = user_cutoff_date.replace(
                month=int(cutoff_month), day=int(cutoff_date))

            comm_exp_acc_id = salesperson_id.commission_expense_account_id
            acc_id = salesperson_id.commission_account_id
            if not commission:
                vals = {'partner_id': salesperson_id.partner_id.id,
                        'start_date': start_date,
                        'end_date': end_date,
                        'sales_limit': salesperson_id.sales_limit,
                        'commission_cut_off_date': commission_cut_off_date,
                        'clinic_id': self.env.user.company_id.id}
                commission = self.create(vals)
            commission._compute_amount()
            return commission or False
        return False

    # @api.multi
    def action_post_expense(self):
        self.ensure_one()
        self.post_sale_commissions()
        return True

    # @api.multi
    def action_cancel_commission(self):
        self.ensure_one()
        if any([line.state == 'paid' for line in self.commission_line_ids]):
            raise UserError(_('You can not cancel the commission once '
                              'commission line has been generated.'))
        self.commission_line_ids.action_cancel()
        self.update({'state': 'cancel'})
        return True

    # @api.multi
    def view_expense_book_entries(self):
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('ref', '=', self.name)],
        }

    # @api.multi
    def update_state(self):
        if all([line.state == 'paid' for line in self.commission_line_ids]):
            self.update({'state': 'paid'})
        return True


class SaleCommissionLine(models.Model):
    _name = "sale.commission.line"
    _description = "Commission Line"
    _order = 'id desc'
    _rec_name = 'commission_id'

    # @api.multi
    def action_view_posted_entries(self):
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('move_id', '=', self.move_id.id)],
        }

    # @api.multi
    def action_cancel(self):
        for line in self:
            line.update({'state': 'cancel'})
        return True

    commission_id = fields.Many2one('sale.commission', string="Commission",
                                    ondelete='cascade', index=True)
    commission_date = fields.Date('Commission Date')
    partner_id = fields.Many2one('res.partner',
                                 related='commission_id.partner_id',
                                 string='Sales Member')
    receipt_commission_id = fields.Many2one('receipt.commission',
                                            string='Receipt Commission Ref.')
    source = fields.Char('Source Document')
    commission_amount = fields.Float(string="Commission Amount")
    payment_amount = fields.Float(string="Payment Amount")
    untaxed_payment_amount = fields.Float(string="Untax Payment Amount")
    taxed_payment_amount = fields.Float(string="Tax Payment Amount")
    currency_id = fields.Many2one('res.currency', 'Currency')
    invoice_id = fields.Many2one('account.move', 'Invoice Ref', copy=False)
    move_id = fields.Many2one('account.move', string="JE Ref.")
    state = fields.Selection([('draft', 'Draft'),
                              ('posted', 'Posted'),
                              ('paid', 'Paid'),
                              ('cancel', 'cancelled')],
                             string='Status', readonly=True,
                             copy=False)

    # @api.multi
    def update_line_state(self):
        for each in self:
            each.update({'state': 'posted'})
        return


class ReceiptCommission(models.Model):
    _name = 'receipt.commission'
    _description = 'Receipt Commission'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', required=True)
    commission_line_id = fields.Many2one('sale.commission.line',
                                         string="Commission Ref.")
    amount = fields.Float(string="Amount")
    date = fields.Date(string="Date")
    state = fields.Selection([('unpaid', 'Unpaid'),
                              ('paid', 'Paid')],
                             default='unpaid',
                             string='Status',
                             copy=False)
    start_date = fields.Date(string="From Date")
    end_date = fields.Date(string="To Date")

    # @api.multi
    def action_view_receipt_commission_payment(self):
        return {
            'name': _('Payments'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('receipt_commission_id', '=', self.id)],
        }
