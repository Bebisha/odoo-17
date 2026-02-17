from odoo import api, fields, models, _
from odoo.addons.base.models.decimal_precision import dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta, TH


class JournalVoucher(models.Model):
    _name = 'journal.voucher'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.depends('line_id.amount')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount = sum(round_curr(line.amount) for line in self.line_id)

    name = fields.Char(string='Journal ID', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', 'Customer', tracking=True, copy=False)
    move_id = fields.Many2one('account.move', 'Journal entry', readonly=True, tracking=True, copy=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', 'Currency', related='company_id.currency_id', tracking=True)
    journal_id = fields.Many2one('account.journal', 'Journal', tracking=True)
    account_id = fields.Many2one('account.account', 'Account', tracking=True)
    date = fields.Date('Date', default=fields.Date.today(), tracking=True)
    # type = fields.Selection([('income', 'Income/Receipt'), ('expense', 'Expense/Payment')], 'Type',default='income')
    state = fields.Selection([('draft', 'Draft'), ('post', 'Post'), ('cancel', 'Cancelled')], 'State', default='draft',
                             tracking=True)
    note = fields.Text('Note', tracking=True)
    line_id = fields.One2many('journal.voucher.line', 'voucher_id', 'Move Lines', copy=True)
    amount = fields.Monetary('Total Amount', readonly=True, store=True, track_visibility='onchange',
                             compute='_compute_amount', )
    cheq_no = fields.Char('Cheque No')
    journal_type = fields.Selection([
        ('sale', 'Sales'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'Miscellaneous'),
    ],
        help="Select 'Sale' for customer invoices journals.\n" \
             "Select 'Purchase' for vendor bills journals.\n" \
             "Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments.\n" \
             "Select 'General' for miscellaneous operations journals.", related='journal_id.type')
    payment_type = fields.Selection([
        ('manual', 'Manual'),
        ('pdc', 'PDC'),
        ('cheque', 'Cheque'),
    ], default="manual", required='1')
    recipt_payment = fields.Selection([
        ('receipt', 'Receipt'),
        ('payment', 'Payment'),
    ], default="receipt", required='1')
    pdc_date = fields.Date('PDC Date', default=fields.Date.today(), tracking=True)
    pdc_cleared = fields.Boolean('PDC Cleared', tracking=True, default=False)
    heading = fields.Char(string="Heading", compute="_get_heading")
    paid_to = fields.Char(string="Paid To")
    received_from = fields.Char(string="Received From")
    inv_number = fields.Char(string='Invoice Number', copy=False)
    invoice_date = fields.Date(string='Invoice Date', copy=False)
    due_date = fields.Date(string='Due Date', copy=False)
    country_code = fields.Char(string='Country Code', related='company_id.country_code')
    reference = fields.Char(string='Reference')
    import_vat = fields.Boolean(string='Import Vat?')

    # def _compute_label(self):
    #     for move in self:
    #         # Get the label from the first line, or any logic you need
    #         if move.line_id:
    #             move.reference = move.line_id[0].label
    #         else:
    #             move.reference = ''



    def _get_heading(self):
        for each in self:
            if each.journal_type == 'bank' and each.payment_type == 'manual' and each.recipt_payment == 'receipt':
                each.heading = 'Bank Receipt Voucher'
            elif each.journal_type == 'bank' and each.payment_type == 'manual' and each.recipt_payment == 'payment':
                each.heading = 'Bank Payment Voucher'
            elif each.journal_type == 'bank' and each.payment_type == 'pdc' and each.recipt_payment == 'receipt':
                each.heading = 'PDC Receipt Voucher'
            elif each.journal_type == 'bank' and each.payment_type == 'pdc' and each.recipt_payment == 'payment':
                each.heading = 'PDC Payment Voucher'
            elif each.journal_type == 'bank' and each.payment_type == 'cheque' and each.recipt_payment == 'receipt':
                each.heading = 'Bank Receipt Voucher'
            elif each.journal_type == 'bank' and each.payment_type == 'cheque' and each.recipt_payment == 'payment':
                each.heading = 'Bank Payment Voucher'
            elif each.journal_type == 'cash' and each.recipt_payment == 'receipt':
                each.heading = 'Cash Receipt Voucher'
            elif each.journal_type == 'cash' and each.recipt_payment == 'payment':
                each.heading = 'Cash Payment Voucher'
            else:
                each.heading = 'Journal Voucher'

    @api.onchange('journal_id', 'type')
    def onchange_journal_type(self):
        for rec in self:
            if rec.journal_id:
                rec.account_id = rec.journal_id.default_account_id and rec.journal_id.default_account_id.id or False

    @api.model
    def create(self, vals):
        # overriding the create method to add the sequence
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('journal.voucher') or _('New')
        result = super(JournalVoucher, self).create(vals)
        return result

    def button_post(self):
        for order in self:
            if order.payment_type == 'pdc' and order.pdc_cleared == False:
                raise ValidationError('Sorry..PDC should be cleared to post the voucher')
            else:
                company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company

                lines = []
                for data in order.line_id:
                    if order.recipt_payment == 'payment':
                        vals = {
                            'account_id': data.account_id.id,
                            'partner_id': data.partner_id.id or False,
                            'name': data.label,
                            'debit': data.amount,
                            'tax_tag_ids': data.tag_ids.ids,
                            'credit': 0,
                        }
                    if order.recipt_payment == 'receipt':
                        vals = {
                            'account_id': data.account_id.id,
                            'partner_id': data.partner_id.id or False,
                            'name': data.label,
                            'tax_tag_ids': data.tag_ids.ids,
                            'credit': data.amount,
                            'debit': 0,
                        }
                    # if data.credit == 0 and data.debit == 0:
                    #     raise ValidationError('Please enter non zero values')
                    # else:
                    lines.append((0, 0, vals))
                if order.recipt_payment == 'payment':
                    l2 = {
                        'account_id': order.account_id.id,
                        'partner_id': order.partner_id.id or False,
                        'name': order.paid_to,
                        'debit': 0,
                        'credit': order.amount,
                    }
                if order.recipt_payment == 'receipt':
                    l2 = {
                        'account_id': order.account_id.id,
                        'partner_id': order.partner_id.id or False,
                        'name': order.received_from,
                        'credit': 0,
                        'debit': order.amount,
                    }
                if order.amount != 0:
                    lines.append((0, 0, l2))
                if order.move_id:
                    self.env['account.move.line'].search([('move_id', '=', order.move_id.id)]).unlink()
                    order.move_id.line_ids = lines
                else:
                    values = {
                        'move_type': 'entry',
                        'currency_id': order.currency_id.id,
                        'date': order.date,
                        'journal_id': order.journal_id.id,
                        'line_ids': lines,
                        'vou_inv_number': order.inv_number,
                        'vou_invoice_date': order.invoice_date,
                        'vou_due_date': order.due_date,
                        'ref': order.reference,
                    }
                    result = self.env['account.move'].create(values)
                    result.action_post()
                    order.move_id = result.id
                order.state = 'post'
        return True

    @api.onchange('line_id', 'import_vat')
    def add_tax_grid(self):
        for rec in self:
            if rec.import_vat:
                grid = self.env['account.account.tag'].search(
                    [('import_vat', '=', True), ('country_id', '=', rec.company_id.country_id.id)], limit=1)
                for line in rec.line_id:
                    line.write({
                        'tag_ids': [(6, 0, [grid.id])],
                    })

    def cancel(self):
        for order in self:
            order.state = 'cancel'
            if order.move_id:
                order.move_id.button_draft()
                order.move_id.button_cancel()
        return

    def reset(self):
        for order in self:
            order.state = 'draft'
        return


class JournalVoucherLine(models.Model):
    _name = 'journal.voucher.line'
    _inherit = ['mail.thread']

    voucher_id = fields.Many2one('journal.voucher', 'Voucher')
    partner_id = fields.Many2one('res.partner', 'Partner')
    account_id = fields.Many2one('account.account', 'Account')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', 'Currency', related='company_id.currency_id', tracking=True)
    label = fields.Char('Label')
    amount = fields.Monetary('Amount')
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')

    tag_ids = fields.Many2many(comodel_name='account.account.tag', string="Tax Grids",
                               help="Tax tags populating this line")

