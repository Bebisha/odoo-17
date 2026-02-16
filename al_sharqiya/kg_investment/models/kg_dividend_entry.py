# -*- coding: utf-8 -*-
from odoo import models, api,fields,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, timezone



class KGDividendEntry(models.Model):
    _name = 'kg.dividend.entry'
    _description = 'Dividend Entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Doc Id',copy=False,
                       readonly=True, index=True, default=lambda self: _('/'))
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date = fields.Date(string='Date',default=fields.Date.today)
    exchange_id = fields.Many2one('kg.exchange',string='Exchange',required=True)
    currency_id = fields.Many2one('res.currency',string='Currency',required=True)
    investment_id = fields.Many2one('kg.investment.entry',string='Investment Entry',required=True)
    investment_type_id = fields.Many2one('kg.investment.type',string='Investment Type',required=True)
    no_of_shares = fields.Float(string='No of Shares',required=True)
    dividend_type = fields.Selection([('stock', 'Stock'),
                                     ('cash', 'Cash')],
                                     default='stock',required=True)
    broker_bank = fields.Selection([('broker', 'Broker'),
                                      ('bank', 'Bank')],
                                      string="Broker/Bank",required=True)
    broker_id = fields.Many2one('res.partner',string='Broker')
    bank_id = fields.Many2one('account.account',string='Bank')
    amount = fields.Monetary(string='Amount')
    memo = fields.Text(string='Memo')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('to_approve', 'To Approve'),
            ('approve', 'Approved'),
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
    journal_entry_ids = fields.One2many('account.move', 'dividend_id', string='Journal Entries')
    manager_approved = fields.Boolean(string='Manager Approval', default=False)
    effective_date = fields.Date(string='Effective Date')
    old_doc_id = fields.Char(string="Old Doc Id")



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('dividend.entry.seq')
        return super(KGDividendEntry, self).create(vals_list)

    @api.onchange('exchange_id')
    def _compute_currency(self):
        for order in self:
            order.currency_id = order.exchange_id.currency_id.id

    @api.onchange('investment_id')
    def _compute_investment_type(self):
        for order in self:
            order.investment_type_id = order.investment_id.investment_type.id

    def action_submit_manager(self):
        for record in self:
            record.manager_approved = True

            receiver = record.env.ref('kg_investment.group_manager')
            partners = []
            subtype_ids = record.env['mail.message.subtype'].search([('res_model', '=', 'kg.purchase.order.')]).ids
            if receiver.users:
                for user in receiver.users:
                    record.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                    partners.append(user.partner_id.id)
                    body = _(u'Dear ' + user.name + '. Please check and approve the this.')
                self.message_post(body=body, partner_ids=partners)

            record.write({'state': 'to_approve'})



    def action_approve(self):
        print("approve")
        for dividend in self:
            if dividend.dividend_type == 'stock':
                dividend.investment_id.purchase_investment(dividend.no_of_shares, 0, 'purchase', dividend.amount)
                stock_journal = dividend.investment_type_id.stock_journal_id  # Assuming investment_type has a field stock_journal_id
                stock_input_account = dividend.investment_type_id.stock_input_account_id  # Assuming investment_type has a field stock_input_account_id
                stock_output_account = dividend.investment_type_id.stock_output_account_id  # Assuming investment_type has a field stock_output_account_id
                if not stock_journal:
                    raise ValidationError("Please set Stock Journal in Investment Type")
                if not stock_input_account:
                    raise ValidationError("Please set Stock Input Account in Investment Type")
                if not stock_output_account:
                    raise ValidationError("Please set Stock Output Account in Investment Type")


                stock_journal_entry = self.env['account.move'].create({
                    'journal_id': stock_journal.id,
                    'date': dividend.effective_date,
                    'ref': dividend.name,
                    'line_ids': [
                        (0, 0, {
                            'name': dividend.investment_id.name,
                            'account_id': stock_input_account.id,
                            'debit': 0.0,
                            'credit': 0.0,
                        }),
                        (0, 0, {
                            'name': dividend.investment_id.name,
                            'account_id': stock_output_account.id,

                            'debit': 0.0,
                            'credit': 0.0,
                            # Assuming net_value represents the value of stock output
                        }),
                    ],
                })
                stock_journal_entry.write({'dividend_id': dividend.id})
                dividend.write({'state': 'approve'})

                # stock_journal_entry.action_post()
            else:
                journal = dividend.env['account.journal'].sudo().search([('name', '=', 'Dividend Journal')], limit=1)
                account_id = self.env['ir.config_parameter'].sudo().get_param('kg_investment.dividend_account_id')

                journal_entry = self.env['account.move'].create({
                    'journal_id': journal.id,
                    'date': dividend.date,
                    'ref': dividend.name,
                    'line_ids': [
                        (0, 0, {
                            'name': dividend.investment_id.name,
                            'account_id': dividend.broker_id.property_account_payable_id.id if dividend.broker_id else dividend.bank_id.id,
                            'partner_id': dividend.broker_id.id if dividend.broker_id else '',
                            # 'debit': dividend.exchange_id.currency_id.rate * dividend.amount,
                            # 'credit': 0.0,
                            'amount_currency': dividend.amount,
                            'currency_id': dividend.currency_id.id,
                            # 'currency_rate':record.exchange_rate,

                        }),
                        (0, 0, {
                            'name': f"{dividend.name} - {dividend.investment_id.name}",
                            'account_id':account_id,
                            # 'debit': 0.0,
                            # 'credit': dividend.exchange_id.currency_id.rate * dividend.amount,
                            'amount_currency': -dividend.amount,
                            'currency_id': dividend.currency_id.id,
                            # 'currency_rate': record.exchange_rate,
                        }),
                    ],
                })
                journal_entry.write({'dividend_id': dividend.id})

                journal_entry.action_post()
                dividend.write({'state': 'posted'})


    def post_dividend_stock_entries(self):
        today = datetime.today().date()
        draft_entries = self.env['account.move'].search([
            ('state', '=', 'draft'),
            ('journal_id.name', '=', 'Dividend Journal'),  # Adjust if needed
            ('date', '=', today),  # Adjust criteria based on your needs
        ])
        # Post each draft journal entry found
        for entry in draft_entries:
            try:
                entry.action_post()
                entry.dividend_id.write({'state': 'posted'})


            except Exception as e:
                pass

    def view_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.journal_entry_ids.ids)],
        }

