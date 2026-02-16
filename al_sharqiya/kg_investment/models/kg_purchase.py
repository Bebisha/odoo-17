# -*- coding: utf-8 -*-
# from cssutils.helper import string
from odoo import models, api,fields,_
from odoo.exceptions import UserError, ValidationError
DEFAULT_DATE_FORMAT = '%d/%m/%Y'

class KGPurchaseOrder(models.Model):
    _name = 'kg.purchase.order'
    _description = 'Purchase'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Doc Id',copy=False,
                       readonly=True, index=True, default=lambda self: _('/'))
    company_id = fields.Many2one('res.company', string='Company', required=True,default=lambda self: self.env.company)
    date = fields.Date(string='Date',default=fields.Date.today)
    exchange_id = fields.Many2one('kg.exchange',string='Exchange',required=True)
    currency_id = fields.Many2one('res.currency',string='Currency',required=True)
    company_currency_id = fields.Many2one('res.currency',string='Currency',default=lambda self: self.env.company.currency_id)
    exchange_rate = fields.Float(string='Exchange Rate',required=True,digits=(16, 6))
    investment_id = fields.Many2one('kg.investment.entry',string='Investment Entry',required=True)
    investment_type_id = fields.Many2one('kg.investment.type',string='Investment Type',required=True)
    reference_no = fields.Many2one('account.move',string='Reference No')
    reference = fields.Char(string='Reference No')
    no_of_shares = fields.Float(string='No of Shares',required=True)
    cost = fields.Float(string='Cost',required=True,digits=(16, 6))
    total_amount = fields.Monetary(string='Total Amount',compute='compute_total_amount',digits=(16, 6))
    broker_bank = fields.Selection([('broker', 'Broker'),
                                    ('bank', 'Bank')],
                                   string="Broker/Bank", required=True)
    broker_id = fields.Many2one('res.partner', string='Broker')
    bank_id = fields.Many2one('account.account', string='Bank')
    commission_type = fields.Selection([('percentage', 'Percentage'),
                                     ('amount', 'Amount')],
                                     default='amount')
    commission = fields.Float(string='Commission',digits=(16, 6))
    total_commission_amount = fields.Monetary(string='Total Commission Amount',compute='compute_total_commission_amount',digits=(16, 6))
    net_value = fields.Monetary(string='Net Value',compute='compute_net_value')
    net_value_base_currency = fields.Float(string='Net Value in Base Currency',compute='compute_net_value_in_base_currency')
    memo = fields.Text(string='Memo')
    manager_approved = fields.Boolean(string='Manager Approval', default=False)
    journal_entry_ids = fields.One2many('account.move', 'purchase_order_id', string='Journal Entries')
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
        default='purchase',
    )
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        check_company=True,
        domain="[('type_tax_use', '=', 'purchase')]",
    )
    tax_amount = fields.Monetary(string='Tax Amount', compute='compute_tax_amount', digits=(10, 6))
    old_doc_id = fields.Char(string="Old Doc Id")
    is_imported = fields.Boolean(string="Imported")



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.seq')
        return super(KGPurchaseOrder, self).create(vals_list)

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
            order.exchange_rate = (order.currency_id.rate)

    @api.onchange('net_value','currency_id')
    def compute_net_value_in_base_currency(self):
        for order in self:
            if order.currency_id != order.company_currency_id:
                order.net_value_base_currency = order.exchange_rate*order.net_value
            else:
                order.net_value_base_currency = order.net_value
    @api.depends('cost','no_of_shares')
    def compute_total_amount(self):
        for order in self:
            order.total_amount = order.no_of_shares * order.cost

    @api.depends('total_amount', 'commission', 'tax_ids')
    def compute_tax_amount(self):
        for record in self:
            taxes = record.tax_ids.compute_all(record.commission, currency=False)['taxes']
            record.tax_amount = sum(tax.get('amount', 0.0) for tax in taxes)
            print("tax_", record.tax_amount)

    @api.depends('total_amount', 'cost', 'no_of_shares', 'commission_type', 'commission', 'tax_ids')
    def compute_total_commission_amount(self):
        for record in self:
            taxes = record.tax_ids.compute_all(record.commission, currency=False)['taxes']
            tax_amount = sum(tax.get('amount', 0.0) for tax in taxes)

            if record.commission_type == 'percentage':
                total_amount_with_tax = record.total_amount + tax_amount
                record.total_commission_amount = (total_amount_with_tax * record.commission) / 100
            else:
                record.total_commission_amount = record.commission + tax_amount
    @api.depends('total_amount','total_commission_amount')
    def compute_net_value(self):
        for order in self:
            order.net_value = order.total_amount + order.total_commission_amount


    def action_submit_manager(self):
        for record in self:
            if not record.investment_id.account_id:
                raise UserError(
                    _('Please set the Account in the Investment Entry before approving the purchase order.'))
            record.manager_approved = True

            receiver = record.env.ref('kg_investment.group_manager')
            partners = []
            subtype_ids = record.env['mail.message.subtype'].search([('res_model', '=', 'kg.purchase.order.')]).ids
            if receiver.users:
                for user in receiver.users:
                    record.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                    partners.append(user.partner_id.id)
                    body = _(u'Dear ' + user.name + '. Please check and approve the Purchase Order.')
                self.message_post(body=body, partner_ids=partners)

            record.write({'state': 'to_approve'})

    def action_approve(self):
        for record in self:
                # Create the journal entry
            journal = record.env['account.journal'].sudo().search([('name', '=', ['Purchase'])], limit=1)
            journal_entry = self.env['account.move'].create({
                'journal_id': journal.id,
                'date': record.date,
                'ref': record.name,
                'line_ids': [
                    (0, 0, {
                        'name': record.investment_id.name,
                        'account_id': record.investment_id.account_id.id,
                        # 'debit': record.net_value_base_currency,
                        # 'credit': 0.0,
                        'amount_currency': record.net_value,
                        'currency_id': record.currency_id.id,
                        # 'currency_rate':record.exchange_rate,

                    }),
                    (0, 0, {
                        'name': record.name,
                        'account_id': record.broker_id.property_account_payable_id.id,
                        'partner_id': record.broker_id.id,
                        # 'debit': 0.0,
                        # 'credit': record.net_value_base_currency,
                        'amount_currency': -record.net_value,
                        'currency_id': record.currency_id.id,
                        # 'currency_rate': record.exchange_rate,
                    }),
                ],
            })
            journal_entry.write({'purchase_order_id':record.id})

            journal_entry.action_post()

            # stock_journal = record.investment_type_id.stock_journal_id # Assuming investment_type has a field stock_journal_id
            # stock_input_account = record.investment_type_id.stock_input_account_id # Assuming investment_type has a field stock_input_account_id
            # stock_output_account = record.investment_type_id.stock_output_account_id # Assuming investment_type has a field stock_output_account_id
            # if not stock_journal:
            #     raise ValidationError("Please set Stock Journal in Investment Type")
            # if not stock_input_account:
            #     raise ValidationError("Please set Stock Input Account in Investment Type")
            # if not stock_output_account:
            #     raise ValidationError("Please set Stock Output Account in Investment Type")

            # stock_journal_entry = self.env['account.move'].create({
            #     'journal_id': stock_journal.id,
            #     'date': record.date,
            #     'ref': record.name,
            #     'line_ids': [
            #         (0, 0, {
            #             'name': record.investment_id.name,
            #             'account_id': stock_input_account.id,
            #             'partner_id': record.broker_id.id,
            #             'amount_currency': record.net_value,
            #             'currency_id': record.currency_id.id,
            #             'debit': record.net_value_base_currency,
            #             'credit': 0.0,
            #         }),
            #         (0, 0, {
            #             'name': record.investment_id.name,
            #             'account_id': stock_output_account.id,
            #             'partner_id': record.broker_id.id,
            #             'amount_currency': -record.net_value,
            #             'currency_id': record.currency_id.id,
            #             'debit': 0.0,
            #             'credit': record.net_value_base_currency,  # Assuming net_value represents the value of stock output
            #         }),
            #     ],
            # })
            # stock_journal_entry.action_post()
            # stock_journal_entry.write({'purchase_order_id': record.id})
        record.investment_id.purchase_investment(record.no_of_shares, record.total_amount, record.type,
                                                         record.cost)

        record.write({'state': 'posted'})
        return {
                'name': _('Journal Entry'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': journal_entry.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
            }

    def view_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.journal_entry_ids.ids)],
        }


