# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError


class KGSaleOrder(models.Model):
    _name = 'kg.sale.order'
    _description = 'Sales'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Doc Id', copy=False,
                       readonly=True, index=True, default=lambda self: _('/'))
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date = fields.Date(string='Date', default=fields.Date.today, date_format='%d/%m/%Y')
    exchange_id = fields.Many2one('kg.exchange', string='Exchange', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    company_currency_id = fields.Many2one('res.currency', string='Currency',
                                          default=lambda self: self.env.company.currency_id)
    exchange_rate = fields.Float(string='Exchange Rate', required=True, digits=(16, 13))
    investment_id = fields.Many2one('kg.investment.entry', string='Investment Name', required=True)
    investment_type_id = fields.Many2one('kg.investment.type', string='Investment Type', required=True)
    reference_no = fields.Many2one('account.move', string='Reference No')
    reference = fields.Char(string='Reference No')
    no_of_shares = fields.Float(string='No of Shares', required=True)
    cost = fields.Float(string='Cost', digits=(10, 6))
    selling_price = fields.Float(string='Selling Price', required=True, digits=(10, 6))
    face_value = fields.Float(string='Face Value/Market Rate', compute='compute_face_value', digits=(10, 6))
    broker_bank = fields.Selection([('broker', 'Broker'),
                                    ('bank', 'Bank')],
                                   string="Broker/Bank", required=True)
    broker_id = fields.Many2one('res.partner', string='Broker')
    bank_id = fields.Many2one('account.account', string='Bank')
    commission_type = fields.Selection([('percentage', 'Percentage'),
                                        ('amount', 'Amount')],
                                       default='amount')
    commission = fields.Float(string='Commission', digits=(16, 6))
    total_commission_amount = fields.Monetary(string='Total Commission Amount',
                                              compute='compute_total_commission_amount', digits=(10, 6))
    net_value = fields.Monetary(string='Net Value', compute='compute_net_value', digits=(10, 6))
    memo = fields.Text(string='Memo')
    manager_approved = fields.Boolean(string='Manager Approval', default=False, copy=False)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('to_approve', 'To Approve'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )
    type = fields.Selection(
        selection=[
            ('purchase', 'Purchase'),
            ('sale', 'Sale'),
        ],
        string='Type',
        default='sale',
    )
    total_amount = fields.Monetary(string='Total Amount', compute='compute_total_amount', digits=(10, 6))
    journal_entry_ids = fields.One2many('account.move', 'kg_sale_id', string='Journal Entries')
    account_id = fields.Many2one('account.account', string='Account')
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        check_company=True,
        domain="[('type_tax_use', '=', 'sale')]",
    )
    tax_amount = fields.Monetary(string='Tax Amount', compute='compute_tax_amount', digits=(10, 6))
    margin = fields.Float(string='Margin', compute='compute_margin', digits=(10, 6))
    net_value_base_currency = fields.Float(string='Net Value in Base Currency',compute='compute_net_value_in_base_currency')
    old_doc_id = fields.Char(string="Old Doc Id")
    is_imported = fields.Boolean(string="Imported")

    @api.onchange('net_value', 'currency_id')
    def compute_net_value_in_base_currency(self):
        for order in self:
            if order.currency_id != order.company_currency_id:
                order.net_value_base_currency = order.exchange_rate * order.net_value
            else:
                order.net_value_base_currency = order.net_value

    @api.onchange('investment_id')
    def _compute_investment_type(self):
        for order in self:
            order.investment_type_id = order.investment_id.investment_type.id

    @api.onchange('exchange_id')
    def _compute_currency(self):
        for order in self:
            order.currency_id = order.exchange_id.currency_id.id

    @api.onchange('currency_id')
    def _compute_exchange_rate(self):
        for order in self:
            order.exchange_rate = order.currency_id.rate

    @api.depends('investment_id')
    def compute_face_value(self):
        for order in self:
            if order.investment_id:
                stock = order.env['market.rate.updation'].search([
                    ('investment_type_id', '=', order.investment_type_id.id),
                    ('state', 'in', ['posted'])
                ],order='id desc')
                if stock:
                    for stock_line in stock.market_rate_line_id:
                        if stock_line.investment_id.id == order.investment_id.id:
                            order.face_value = stock_line.market_rate
                            break  # Found matching stock line, set face_value and exit loop
                    else:
                        order.face_value = order.investment_id.face_value  # No matching stock line, use investment_id face_value
                else:
                    order.face_value = order.investment_id.face_value  # No stock found, use investment_id face_value
            else:
                order.face_value = 0.0
            print("face val",order.face_value)

    @api.depends('selling_price', 'no_of_shares')
    def compute_total_amount(self):
        for order in self:
            order.total_amount = (order.no_of_shares * order.selling_price)

    @api.depends('selling_price', 'face_value')
    def compute_margin(self):
        for order in self:
            order.margin = order.selling_price - order.face_value

    @api.depends('total_amount', 'commission', 'tax_ids')
    def compute_tax_amount(self):
        for record in self:
            taxes = record.tax_ids.compute_all(record.commission, currency=False)['taxes']
            record.tax_amount = sum(tax.get('amount', 0.0) for tax in taxes)
            print("tax_",record.tax_amount)


    # @api.depends('selling_price', 'no_of_shares', 'commission_type', 'commission')
    # def compute_total_commission_amount(self):
    #     for record in self:
    #         if record.commission_type == 'percentage':
    #             record.total_commission_amount = (record.selling_price * record.no_of_shares * record.commission) / 100
    #         else:
    #             record.total_commission_amount = record.commission

    @api.depends('total_amount', 'selling_price', 'no_of_shares', 'commission_type', 'commission', 'tax_ids')
    def compute_total_commission_amount(self):
        for record in self:
            taxes = record.tax_ids.compute_all(record.commission, currency=False)['taxes']
            tax_amount = sum(tax.get('amount', 0.0) for tax in taxes)
            print("tax_amount2",tax_amount)

            if record.commission_type == 'percentage':
                total_amount_with_tax = record.total_amount + tax_amount
                record.total_commission_amount = (total_amount_with_tax * record.commission) / 100
            else:
                record.total_commission_amount = record.commission + tax_amount

    @api.depends('total_amount', 'total_commission_amount')
    def compute_net_value(self):
        for order in self:
            order.net_value = order.total_amount - order.total_commission_amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.order.seq')
        return super(KGSaleOrder, self).create(vals_list)

    def view_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.journal_entry_ids.ids)],
        }

    def action_submit_manager(self):
        for record in self:
            if not record.investment_id.account_id:
                raise UserError(
                    _('Please set the Account in the Investment Entry before Submitting the  order.'))
            receiver = record.env.ref('kg_investment.group_manager')
            print("receiver", receiver)
            partners = []
            subtype_ids = record.env['mail.message.subtype'].search([('res_model', '=', 'kg.purchase.order.')]).ids
            if receiver.users:
                print("user", receiver.users)
                for user in receiver.users:
                    record.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                    partners.append(user.partner_id.id)
                    body = _(u'Dear ' + user.name + '. Please check and approve the Sale Order.')
                self.message_post(body=body, partner_ids=partners)
                record.manager_approved = True

            record.write({'state': 'to_approve'})

    def action_approve(self):
        for record in self:
            # Create the journal entry
            journal = record.env['account.journal'].sudo().search([('name', '=', ['Sales', ])], limit=1)

            if record.investment_type_id.is_fvtpl:
                journal_lines = []
                account_id = self.env['ir.config_parameter'].sudo().get_param('kg_investment.market_fvtpl_account_id')
                print("account_id1", account_id)
                if not account_id:
                    raise ValidationError("Please set Account in Settings")

                journal_entry_lines = [
                    (0, 0, {
                        'name': record.investment_id.name,
                        'account_id': record.investment_id.account_id.id,
                        'amount_currency': round(-(record.face_value * record.no_of_shares), 13),
                        'currency_id': record.currency_id.id,
                        # 'debit': 0.0,
                        # 'credit': round((record.face_value * record.no_of_shares) * record.exchange_rate, 13),
                    }),
                    (0, 0, {
                        'name': record.name,
                        'account_id': record.investment_type_id.market_account_id.id,
                        'amount_currency': round(-((record.selling_price - record.face_value) * record.no_of_shares), 13),
                        'currency_id': record.currency_id.id,
                        # 'debit': 0.0,
                        # 'credit': round((record.selling_price - record.face_value) * record.no_of_shares * record.exchange_rate,
                        #                 13),
                    }),
                    (0, 0, {
                        'name': record.name,
                        'account_id':  record.broker_id.property_account_receivable_id.id if record.broker_id else record.bank_id.id,
                        'partner_id':record.broker_id.id if record.broker_id else '',
                        'currency_id': record.currency_id.id,
                        'amount_currency': round(record.selling_price * record.no_of_shares, 13),
                        # 'debit': round(record.selling_price * record.no_of_shares * record.exchange_rate, 13),
                        # 'credit': 0.0,
                    }),
                ]

                print("journal_entry_lines", journal_entry_lines)
                # Check if there is commission and add commission lines if needed
                if record.commission != False:
                    commission_debit_account_id = account_id  # Replace with appropriate account ID for commission debit
                    commission_credit_account_id = record.account_id.id  # Replace with appropriate account ID for commission credit

                    commission_debit_line = (0, 0, {
                        'name': 'Commission',
                        'account_id': commission_debit_account_id,
                        # 'debit': record.total_commission_amount * record.exchange_rate,
                        # 'credit': 0.0,
                        'amount_currency': record.total_commission_amount,
                        'currency_id': record.currency_id.id,
                    })

                    commission_credit_line = (0, 0, {
                        'name': 'Commission',
                        'account_id': record.investment_type_id.market_account_id.id,
                        # 'debit': 0.0,
                        # 'credit': record.total_commission_amount * record.exchange_rate,
                        'amount_currency': -(record.total_commission_amount),
                        'currency_id': record.currency_id.id,

                    })

                    journal_entry_lines.append(commission_debit_line)
                    journal_entry_lines.append(commission_credit_line)

                # Create the journal entry
                journal_entry = self.env['account.move'].create({
                    'journal_id': journal.id,
                    'date': record.date,
                    'ref': record.name,
                    'kg_sale_id': record.id,
                    'line_ids': journal_entry_lines,
                })

                journal_entry.action_post()

            elif record.investment_type_id.is_fvoci:
                journal_entry_lines = []
                fvoci_account_id = self.env['ir.config_parameter'].sudo().get_param(
                    'kg_investment.market_fvoci_account_id')
                bank_broker_account_amount = (record.selling_price * record.no_of_shares) - record.total_commission_amount if record.total_commission_amount else record.selling_price * record.no_of_shares
                investment_account_amount = record.face_value * record.no_of_shares
                retained_account_amount = ((record.selling_price-record.investment_id.face_value) * record.no_of_shares)-(record.total_commission_amount-record.tax_amount) if record.total_commission_amount else (record.selling_price-record.investment_id.face_value) * record.no_of_shares

                revaluation_account = self.env['account.account'].search([('id', '=', record.investment_id.revaluation_account_id.id)])
                if revaluation_account:
                    revaluation_account_balance = revaluation_account.current_balance
                else:
                    revaluation_account_balance =0.0
                investment = self.env['kg.investment.entry'].search([('id', '=', record.investment_id.id)])
                if investment:
                    total_shares = investment.qty_on_hand
                else:
                    total_shares = 0.0
                revaluation_account_amount =  (revaluation_account_balance / total_shares) * record.no_of_shares

                if not fvoci_account_id:
                    raise ValidationError("Please set Account in Settings")
                if not record.investment_id.revaluation_account_id:
                    raise ValidationError("Please set Revaluation Account in Investment Entry")


                journal_entry_lines = [
                    (0, 0, {
                        'name': record.investment_id.name,
                        'account_id': record.investment_id.account_id.id,
                        'amount_currency': -investment_account_amount,
                        'currency_id': record.currency_id.id,
                        # 'debit': 0.0,
                        # 'credit': (record.face_value * record.no_of_shares) * record.exchange_rate,
                    }),
                    (0, 0, {
                        'name': record.name,
                        'account_id': fvoci_account_id,
                        'partner_id': record.broker_id.id,
                        'currency_id': record.currency_id.id,
                        'amount_currency': -retained_account_amount if record.selling_price>record.investment_id.face_value else retained_account_amount,
                        # 'debit': 0.0,
                        # 'credit': retained_credit * record.exchange_rate,
                        # 'credit': ((record.investment_id.face_value - record.selling_price) * record.no_of_shares) * record.exchange_rate,
                    }),
                    (0, 0, {
                        'name': record.name,
                        'account_id': record.investment_id.revaluation_account_id.id,
                        'currency_id': record.currency_id.id,
                        'amount_currency': revaluation_account_amount,
                        # 'debit': ((record.selling_price - record.face_value) * record.no_of_shares) * record.exchange_rate,
                        # 'credit': 0.0,
                    }),

                    (0, 0, {
                        'name': record.investment_id.name,
                        'account_id': record.broker_id.property_account_payable_id.id if record.broker_id else record.bank_id.id,
                        'partner_id': record.broker_id.id if record.broker_id else '',
                        'amount_currency': bank_broker_account_amount,
                        'currency_id': record.currency_id.id,
                        # 'debit': (record.selling_price * record.no_of_shares) * record.exchange_rate,
                        # 'credit': 0.0,
                    }),

                ]
                if record.tax_ids:
                    tax_accounts = record.tax_ids.mapped('invoice_repartition_line_ids.account_id')
                    print("tax_accountssssss",tax_accounts)

                    commission_debit_account_id = tax_accounts.id
                    commission_credit_account_id = record.account_id.id  # Replace with appropriate account ID for commission credit

                    commission_debit_line = (0, 0, {
                        'name': 'Commission',
                        'account_id': commission_debit_account_id,
                        # 'debit': record.total_commission_amount * record.exchange_rate,
                        # 'credit': 0.0,
                        'currency_id': record.currency_id.id,
                        'amount_currency': record.tax_amount

                    })

                    # commission_credit_line = (0, 0, {
                    #     'name': 'Commission',
                    #     'account_id': commission_credit_account_id,
                    #     'partner_id': record.broker_id.id,
                    #     # 'debit': 0.0,
                    #     # 'credit': record.total_commission_amount * record.exchange_rate,
                    #     'currency_id': record.currency_id.id,
                    #     'amount_currency': -(record.total_commission_amount)
                    # })

                    journal_entry_lines.append(commission_debit_line)
                    # journal_entry_lines.append(commission_credit_line)
                journal_entry = self.env['account.move'].create({
                    'journal_id': journal.id,
                    'date': record.date,
                    'ref': record.name,
                    'kg_sale_id': record.id,
                    'line_ids': journal_entry_lines,
                })

                journal_entry.action_post()
            record.investment_id.sale_investment(record.no_of_shares, record.total_amount, record.type, record.selling_price)
            record.write({'state': 'posted'})
