from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from datetime import date, datetime, timedelta


class AccountMoveInherit(models.Model):
    _inherit = 'account.payment'

    payment_lines_ids = fields.One2many('payment.allocation.lines', 'payment_id')
    kg_invoice_ids = fields.Many2many('account.move', 'account_move_rel_2', string='Select invoices')
    partner_invoice_id = fields.Many2many('account.move', 'account_move_rel_3', string='Partner Invoice')
    is_full_reconcile = fields.Boolean(default=False, copy=False)

    # @api.constrains('payment_lines_ids')
    # def check_allocation(self):
    #     tot_allocate = sum(self.payment_lines_ids.mapped('allocated_amount'))
    #     if self.env.context.get('direct_creation'):
    #         if self.amount < tot_allocate:
    #             raise ValidationError("Amount must be greater than equal to total allocated amount")

    @api.model
    def create(self, vals):
        res = super(AccountMoveInherit, self).create(vals)
        if 'payment_lines_ids' in vals.keys():
            lines = vals.get('payment_lines_ids')
            for line in lines:
                alloc = self.env['advance.allocations'].search(
                    [('invoice_id', '=', line[2].get('invoice_line_id')), ('payment_id', '=', res.id)])
                if len(alloc) == 1:
                    alloc.amount = line[2].get('allocated_amount')
                else:
                    env = self.env['advance.allocations'].create(
                        {'type': 'payment', 'payment_id': res.id, 'amount': line[2].get('allocated_amount'),
                         'pdc_id': False,
                         'invoice_id': line[2].get('invoice_line_id')})
        return res

    def write(self, vals):
        if 'payment_lines_ids' in vals.keys():
            lines = vals.get('payment_lines_ids')
            for line in lines:
                alc_line = self.env['payment.allocation.lines'].browse(line[1])
                alloc = self.env['advance.allocations'].search(
                    [('invoice_id', '=', alc_line.invoice_line_id.id), ('payment_id', '=', self.id)])
                if len(alloc) == 1:
                    alloc.amount = line[2].get('allocated_amount')
                else:
                    env = self.env['advance.allocations'].create(
                        {'type': 'payment', 'payment_id': self.id, 'amount': line[2].get('allocated_amount'),
                         'pdc_id': False,
                         'invoice_id': line[2].get('invoice_line_id')})
        return super(AccountMoveInherit, self).write(vals)

    def action_draft(self):
        self.is_full_reconcile = False
        return super(AccountMoveInherit, self).action_draft()

    def action_post(self):
        res = super(AccountMoveInherit, self).action_post()
        tot_allocate = sum(self.payment_lines_ids.mapped('allocated_amount'))
        #
        if self.env.context.get('direct_creation'):
            self.validate_payment()
        self.is_full_reconcile = True
        for line in self.payment_lines_ids:
            alloc = self.env['advance.allocations'].search(
                [('invoice_id', '=', line.invoice_line_id.id), ('payment_id', '=', self.id)])
            if len(alloc) == 1:
                alloc.amount = line.allocated_amount
            else:
                self.env['advance.allocations'].create(
                    {'type': 'payment', 'payment_id': self.id, 'amount': line.allocated_amount, 'pdc_id': False,
                     'invoice_id': line.invoice_line_id.id})
        return res

    @api.onchange('partner_id', 'payment_type')
    def _onchange_partner_invoices(self):
        list = []
        for rec in self:
            if rec.kg_invoice_ids:
                rec.kg_invoice_ids = False
            if rec.partner_id:
                if rec.payment_type == 'inbound':
                    account_move_id = self.env['account.move'].search(
                        [('state', 'not in', ['draft', 'cancel']), ('payment_state', 'in', ['not_paid', 'partial']),
                         ('move_type', '=', 'out_invoice'), ('partner_id', '=', rec.partner_id.id)])
                    # if not account_move_id:
                    #     raise UserError(_('There is no due amount for this customer'))
                    if account_move_id:
                        for inv in account_move_id:
                            pdc = self.env['advance.allocations'].search(
                                [('invoice_id', '=', inv.id), ('type', '=', 'pdc'),
                                 ('pdc_state', 'in', ['registered', 'deposited'])])
                            pdc_amount = sum(pdc.mapped('amount'))
                            payment = self.env['advance.allocations'].search(
                                [('invoice_id', '=', inv.id), ('type', '=', 'payment'),
                                 ('payment_state', '=', 'draft'), ('payment_id.is_full_reconcile', '=', False)])
                            payment_amount = sum(payment.mapped('amount'))
                            if inv.amount_residual - (pdc_amount + payment_amount) > 0:
                                list.append(inv.id)
                    rec.partner_invoice_id = list
                if rec.payment_type == 'outbound':
                    account_move_id = self.env['account.move'].search(
                        [('state', 'not in', ['draft', 'cancel']), ('payment_state', 'in', ['not_paid', 'partial']),
                         ('move_type', '=', 'in_invoice'), ('partner_id', '=', rec.partner_id.id)])
                    # if not account_move_id:
                    #     raise UserError(_('There is no due amount for this customer'))
                    if account_move_id:
                        for inv in account_move_id:
                            pdc = self.env['advance.allocations'].search(
                                [('invoice_id', '=', inv.id), ('type', '=', 'pdc'),
                                 ('pdc_state', 'in', ['registered', 'deposited'])])
                            pdc_amount = sum(pdc.mapped('amount'))
                            payment = self.env['advance.allocations'].search(
                                [('invoice_id', '=', inv.id), ('type', '=', 'payment'),
                                 ('payment_state', '=', 'draft'), ('payment_id.is_full_reconcile', '=', False)])
                            payment_amount = sum(payment.mapped('amount'))
                            if inv.amount_residual - (pdc_amount + payment_amount) > 0:
                                list.append(inv.id)
                    rec.partner_invoice_id = list

    @api.onchange('partner_id')
    def default_invoice(self):
        if self.payment_type == 'inbound':
            invoice = self.partner_id.invoice_ids.filtered(
                lambda rec: rec.amount_residual and rec.state == 'posted' and rec.move_type == 'out_invoice')

            self.kg_invoice_ids = False
            for inv in invoice:
                pdc = self.env['advance.allocations'].search(
                    [('invoice_id', '=', inv.id), ('type', '=', 'pdc'),
                     ('pdc_state', 'in', ['registered', 'deposited'])])
                pdc_amount = sum(pdc.mapped('amount'))
                payment = self.env['advance.allocations'].search(
                    [('invoice_id', '=', inv.id), ('type', '=', 'payment'),
                     ('payment_state', '=', 'draft'), ('payment_id.is_full_reconcile', '=', False)])
                payment_amount = sum(payment.mapped('amount'))
                unallocated_amount = inv.amount_residual - (pdc_amount + payment_amount)
                if unallocated_amount > 0:
                    self.kg_invoice_ids = [(4, inv.id)]
        else:
            invoice_new = self.partner_id.invoice_ids.filtered(
                lambda rec: rec.amount_residual and rec.state == 'posted' and rec.move_type == 'in_invoice')
            self.kg_invoice_ids = False
            for inv in invoice_new:
                pdc = self.env['advance.allocations'].search(
                    [('invoice_id', '=', inv.id), ('type', '=', 'pdc'),
                     ('pdc_state', 'in', ['registered', 'deposited'])])
                pdc_amount = sum(pdc.mapped('amount'))
                payment = self.env['advance.allocations'].search(
                    [('invoice_id', '=', inv.id), ('type', '=', 'payment'),
                     ('payment_state', '=', 'draft'), ('payment_id.is_full_reconcile', '=', False)])
                payment_amount = sum(payment.mapped('amount'))
                unallocated_amount = inv.amount_residual - (pdc_amount + payment_amount)
                if unallocated_amount > 0:
                    self.kg_invoice_ids = [(4, inv.id)]

    @api.onchange('kg_invoice_ids')
    def _onchange_move_del(self):
        data = []
        for rec in self:
            if rec.kg_invoice_ids:
                for i in rec.kg_invoice_ids:
                    val_2 = 0
                    if i._origin.move_type == 'out_invoice':
                        if i._origin.line_ids.filtered(lambda l: l.credit == 0):
                            val_2 = i._origin.line_ids.filtered(lambda l: l.credit == 0)[0].id
                    elif i._origin.move_type == 'in_invoice':
                        if i._origin.line_ids.filtered(lambda l: l.debit == 0):
                            val_2 = i._origin.line_ids.filtered(lambda l: l.debit == 0)[0].id
                    pdc = self.env['advance.allocations'].search(
                        [('invoice_id', '=', i._origin.id), ('type', '=', 'pdc'),
                         ('pdc_state', 'in', ['registered', 'deposited'])])
                    pdc_amount = sum(pdc.mapped('amount'))
                    payment = self.env['advance.allocations'].search(
                        [('invoice_id', '=', i._origin.id), ('type', '=', 'payment'),
                         ('payment_state', '=', 'draft'), ('payment_id.is_full_reconcile', '=', False)])
                    allocation_entry = pdc + payment
                    payment_amount = sum(payment.mapped('amount'))
                    vals = {
                        'name': i.name,
                        'invoice_date': i.invoice_date,
                        'invoice_date_due': i.invoice_date_due,
                        'amount_total_signed': abs(i.amount_total),
                        'amount_residual': abs(i.amount_residual),
                        'allocated_amount':0.00,
                        # 'allocated_amount': abs(i.amount_residual_signed) - (pdc_amount + payment_amount),
                        'invoice_line_id': i.id,
                        'po_number': i.line_ids.purchase_line_id.order_id.name,
                        # 'supplier_ref': i.supplier_ref ,
                        'ref': i.ref,
                        'inv_line_id': val_2,

                    }
                    data.append((0, 0, vals))


        self.payment_lines_ids = False
        self.write({'payment_lines_ids': data})


    def validate_payment(self):
        for invoice in self.payment_lines_ids:
            deposited_credit = self.move_id.line_ids.filtered(lambda x: x.credit > 0)
            deposited_debit = self.move_id.line_ids.filtered(lambda x: x.debit > 0)
            inv = self.env['account.move'].sudo().search([('name', '=', invoice.name),('company_id','=',self.company_id.id)])
            if self.payment_type == 'inbound':
                debit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', inv.id),
                                                                             ('debit', '>', 0.0)], limit=1)

                credit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', self.move_id.id),
                                                                              ('credit', '>', 0.0)], limit=1)

                if debit_move_id and credit_move_id:
                    if invoice.allocated_amount > 0.00:
                        reconcile_id = self.env['account.partial.reconcile'].sudo().create(
                            {'debit_move_id': debit_move_id.id,
                             'credit_move_id': credit_move_id.id,
                             'amount': invoice.allocated_amount,
                             'debit_amount_currency': invoice.allocated_amount,
                             'credit_amount_currency': invoice.allocated_amount,
                             })
                        # reconcile_id = self.env['account.partial.reconcile'].sudo().create(
                        #     {'debit_move_id': deposited_debit.id,
                        #      'credit_move_id': credit_move_id.id,
                        #      'amount': invoice.allocated_amount,
                        #      'debit_amount_currency': invoice.allocated_amount,
                        #      'credit_amount_currency': invoice.allocated_amount,
                        #      })
            else:
                # reconcilation Entry for Invoice
                credit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', inv.id),
                                                                              ('credit', '>', 0.0)], limit=1)

                debit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', self.move_id.id),
                                                                             ('debit', '>', 0.0)], limit=1)

                if debit_move_id and credit_move_id:
                    if invoice.allocated_amount > 0.00:
                        reconcile_id = self.env['account.partial.reconcile'].sudo().create(
                            {'debit_move_id': debit_move_id.id,
                             'credit_move_id': credit_move_id.id,
                             'amount': invoice.allocated_amount,
                             'debit_amount_currency': invoice.allocated_amount,
                             'credit_amount_currency': invoice.allocated_amount,
                             })

    def action_open_payment_wizard(self):
        payment_vals = []
        partner = False
        def_id = False
        company = False
        inv_vals = []
        for data in self:
            if partner != data.partner_id.id and partner != False:
                raise ValidationError(_('Selected Payments are of different Partners'))

            if data.is_reconciled:
                raise ValidationError(_('Already Reconciled'))

            val_1 = 0
            for line in self.line_ids:
                # Exta condition added (inbound/outbound)
                if self.payment_type == 'inbound':
                    if line.debit == 0:
                        val_1 = line.id
                if self.payment_type == 'outbound':
                    if line.credit == 0:
                        val_1 = line.id
            debit = self.env['account.partial.reconcile'].search([('credit_move_id', '=', val_1)])
            amount_bal = 0
            for val in debit:
                amount_bal += val.debit_amount_currency
            payment_vals.append({
                'name': data.name,
                'date': data.date,
                'memo': data.ref,
                'move_line_id': val_1,
                'amount': data.amount if not debit else data.amount - amount_bal})

            partner = data.partner_id.id
            def_id = data.id
            company = data.company_id.id
            invoice = self.env['account.move'].search([('partner_id', '=', data.partner_id.id),
                                                       ('payment_state', 'in', ['partial', 'not_paid', 'in_payment']),
                                                       ('amount_residual', '!=', 0.0), ('state', 'in', ['posted'])])

            for inv in invoice:
                val_2 = 0

                if inv.move_type == 'out_invoice':
                    if inv.line_ids.filtered(lambda l: l.credit == 0):
                        val_2 = inv.line_ids.filtered(lambda l: l.credit == 0)[0].id
                elif inv.move_type == 'in_invoice':
                    if inv.line_ids.filtered(lambda l: l.debit == 0):
                        val_2 = inv.line_ids.filtered(lambda l: l.debit == 0)[0].id
                inv_vals.append({'inv_amount': inv.amount_total,
                                 'name': inv.name,
                                 'inv_date': inv.invoice_date,
                                 'move_line_id': val_2,
                                 'date_due': inv.invoice_date_due,
                                 'inv_unallocated_amount': inv.amount_residual,

                                 })
        return {
            'name': 'Payment',
            'res_model': 'payment.allocation.wizard',
            'type': 'ir.actions.act_window',
            'context': {'default_partner_id': partner,
                        'default_payment_id': def_id,
                        'default_payment_type': data.payment_type,
                        'default_balnc_paymnt_amnt': data.amount if not debit else data.amount - amount_bal,
                        'default_payment_allocation_ids': payment_vals,
                        'default_invoice_allocation_ids': inv_vals,
                        'default_company_id': company,

                        },
            'view_type': 'form',
            'view_mode': 'form,list',
            'target': 'new'}



class PaymentAllocationLines(models.TransientModel):
    _name = "payment.allocation.lines"
    _description = 'Allocation Lines'

    payment_id = fields.Many2one('account.payment')
    name = fields.Char(string='Invoice Number')
    po_number = fields.Char(string='Purchase Number')
    ref = fields.Char(string='Bill Reference')
    supplier_ref = fields.Char(string='Sup PO')
    currency_id = fields.Many2one(
        'res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    invoice_date = fields.Date(string='Invoice Date')
    invoice_date_due = fields.Date(string='Due Date')
    amount_total_signed = fields.Monetary(string='Invoice Amount')
    amount_residual = fields.Monetary(string='Due Amount')
    allocated_amount = fields.Float('Allocated Amount')
    invoice_line_id = fields.Many2one('account.move', "Invoice Id")
    inv_line_id = fields.Many2one('account.move.line', "Invoice Line Id")
    alrdy_allocated = fields.Float('Already Allocated Amount', compute='get_alrdy_allocated')
    allocation_ids = fields.Many2many('advance.allocations', compute='get_alrdy_allocated')

    @api.constrains('allocated_amount')
    def check_allocated_amount(self):
        for rec in self:
            if rec.allocated_amount > rec.amount_residual:
                raise ValidationError("Allocated amount must be less than or equal to due amount")

    @api.depends('invoice_line_id')
    def get_alrdy_allocated(self):
        for rec in self:
            pdc_payments = self.env['advance.allocations'].search([
                ('invoice_id', '=', rec.invoice_line_id.id),
                ('type', 'in', ['pdc', 'payment']),
                ('pdc_state', 'in', ['registered', 'deposited']),
                '|',
                ('payment_state', '=', 'draft'),
                ('payment_id.is_full_reconcile', '=', False)
            ])

            allocation_amount = sum(pdc_payments.filtered(lambda x: x.type == 'pdc').mapped('amount'))
            payment_amount = sum(pdc_payments.filtered(lambda x: x.type == 'payment').mapped('amount'))

            rec.allocation_ids = [(6, 0, pdc_payments.ids)]
            rec.alrdy_allocated = allocation_amount + payment_amount


class AccountPaymentRegisterInh(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        payments = self._create_payments()
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        if active_ids and active_model == 'account.move':
            invoices = self.env['account.move'].browse(active_ids)
            data = []
            for invoice in invoices:
                pdc = self.env['advance.allocations'].search(
                    [('invoice_id', '=', invoice.id), ('type', '=', 'pdc'),
                     ('pdc_state', 'in', ['registered', 'deposited'])])
                pdc_amount = sum(pdc.mapped('amount'))
                payment = self.env['advance.allocations'].search(
                    [('invoice_id', '=', invoice.id), ('type', '=', 'payment'),
                     ('payment_state', '=', 'draft'), ('payment_id.is_full_reconcile', '=', False)])
                payment_amount = sum(payment.mapped('amount'))
                unallocated_amount = invoice.amount_residual - (pdc_amount + payment_amount)
                val_2 = 0

                if invoice.move_type == 'out_invoice':
                    if invoice.line_ids.filtered(lambda l: l.credit == 0):
                        val_2 = invoice.line_ids.filtered(lambda l: l.credit == 0)[0].id
                elif invoice.move_type == 'in_invoice':
                    if invoice.line_ids.filtered(lambda l: l.debit == 0):
                        val_2 = invoice.line_ids.filtered(lambda l: l.debit == 0)[0].id
                if unallocated_amount >= self.amount:
                    payments.kg_invoice_ids = [(4, invoice.id)]
                    vals = {
                        'name': invoice.name,
                        'invoice_date': invoice.invoice_date,
                        'invoice_date_due': invoice.invoice_date_due,
                        'amount_total_signed': invoice.amount_total_signed,
                        'amount_residual': invoice.amount_residual_signed,
                        'allocated_amount': self.amount,
                        'invoice_line_id': invoice.id,
                        'inv_line_id': val_2,
                        'alrdy_allocated': pdc_amount + payment_amount,
                    }
                    data.append((0, 0, vals))
                # else:
                #     raise UserError("Payment Amount exceeded..")
            payments.payment_lines_ids = data

        if self._context.get('dont_redirect_to_payments'):
            return True

        action = {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'context': {'create': False},
        }
        if len(payments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': payments.id,
            })
        else:
            action.update({
                'view_mode': 'tree,form',
                'domain': [('id', 'in', payments.ids)],
            })
        return action
