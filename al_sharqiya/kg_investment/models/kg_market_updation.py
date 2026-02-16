# -*- coding: utf-8 -*-
from odoo import models, api,fields,_
from odoo.exceptions import UserError, ValidationError


class KGMarketRateUpdation(models.Model):
    _name = 'market.rate.updation'
    _description = 'Market Rate Updation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Doc Id',copy=False,
                       readonly=True, index=True, default=lambda self: _('/'))
    company_id = fields.Many2one('res.company', string='Company', required=True,default=lambda self: self.env.company)
    date = fields.Date(string='Date',default=fields.Date.today)
    updated_on = fields.Date(string='Updated On')
    currency_id = fields.Many2one('res.currency',string='Currency',required=True)
    investment_type_id = fields.Many2one('kg.investment.type',string='Investment Type',required=True)
    market_rate_line_id = fields.One2many('market.rate.line','market_rate_id')


    # investment_name = fields.Char(string='Investment Name')
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
    manager_approved = fields.Boolean(string='Manager Approval', default=False)
    journal_entry_ids = fields.One2many('account.move', 'market_rate_id', string='Journal Entries')



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('market.rate.seq')
        return super(KGMarketRateUpdation, self).create(vals_list)

    def action_confirm(self):
        print("confirm")

    @api.onchange('investment_type_id')
    def onchange_investment_type_id(self):
        if self.investment_type_id:
            investment_entries = self.env['kg.investment.entry'].search(
                [('investment_type', '=', self.investment_type_id.id)])
            lines = []
            seen_investment_ids = set()  # To track seen investment_ids

            for entry in investment_entries:
                if entry.id in seen_investment_ids:
                    continue  # Skip this entry if investment_id has already been added
                lines.append((0, 0, {
                    'investment_id': entry.id,
                    'available_shares': entry.qty_on_hand,
                    'face_value': entry.face_value,
                    'market_rate': entry.face_value,
                }))

                seen_investment_ids.add(entry.id)
                print("entry==",entry.name)
                print("faceeee==",entry.face_value)
            self.market_rate_line_id = False  # Clear existing lines
            self.market_rate_line_id = lines

    def action_submit_manager(self):
        for record in self:
            record.manager_approved = True
            if not record.investment_type_id.market_account_id:
                raise UserError(
                    _('Please set the Account in the Investment Type before submitting this.'))
            receiver = record.env.ref('kg_investment.group_manager')
            partners = []
            subtype_ids = record.env['mail.message.subtype'].search([('res_model', '=', 'kg.purchase.order.')]).ids
            if receiver.users:
                for user in receiver.users:
                    record.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                    partners.append(user.partner_id.id)
                    body = _(u'Dear ' + user.name + '. Please check and approve this.')
                self.message_post(body=body, partner_ids=partners)

            record.write({'state': 'to_approve'})

    def action_approve(self):
        for record in self:
            journal = record.env['account.journal'].sudo().search([('name', '=', 'Market Rate Journal')], limit=1)

            if record.investment_type_id.is_fvtpl :
                journal_lines = []
                for line in record.market_rate_line_id:
                    # Accumulate debit and credit amounts for each line
                    t_amount = line.available_shares * line.market_rate
                    amount = t_amount
                    # amount = t_amount * record.currency_id.rate

                    # Create journal entry lines for each line in market rate line id
                    journal_lines.append((0, 0, {
                        'name': line.investment_id.name,
                        'account_id': line.investment_id.account_id.id,
                        # 'debit': 0.0,
                        # 'credit': amount,
                        'amount_currency': -t_amount,
                        'currency_id': record.currency_id.id,
                    }))
                    journal_lines.append((0, 0, {
                        'name': record.name,
                        'account_id': record.investment_type_id.market_account_id.id,
                        # 'debit': amount,
                        # 'credit': 0.0,
                        'amount_currency': t_amount,
                        'currency_id': record.currency_id.id,
                    }))

                # Create the journal entry with accumulated amounts
                journal_entry = self.env['account.move'].create({
                    'journal_id': journal.id,
                    'date': record.date,
                    'ref': record.name,
                    'line_ids': journal_lines,
                    'market_rate_id':record.id,
                })
                journal_entry.action_post()
                print("journal_entry",journal_entry)
            if record.investment_type_id.is_fvoci:
                journal_lines = []

                for line in record.market_rate_line_id:
                    # Accumulate debit and credit amounts for each line
                    current_market_value = line.investment_id.market_value
                    current_face_value = line.investment_id.face_value
                    current_market_rate = line.market_rate

                    if current_market_value > 0:
                        revaluation_amount = (current_market_value - current_market_rate) * line.available_shares
                    else:
                        revaluation_amount = (current_face_value - current_market_rate) * line.available_shares

                    # Determine amount_currency based on the conditions
                    if current_market_value > 0:
                        if current_market_value < current_market_rate:
                            amount_currency = revaluation_amount
                        else:
                            amount_currency=revaluation_amount

                    else:
                        amount_currency = -revaluation_amount if current_face_value < current_market_rate else revaluation_amount

                    # Create journal entry lines for each line in market rate line id
                    journal_lines.append((0, 0, {
                        'name': line.investment_id.name,
                        'account_id': line.investment_id.revaluation_account_id.id,
                        'amount_currency': amount_currency,
                        'currency_id': record.currency_id.id,
                    }))
                    journal_lines.append((0, 0, {
                        'name': record.name,
                        'account_id': line.investment_id.account_id.id,
                        'amount_currency': -amount_currency,  # opposite amount for the other account
                        'currency_id': record.currency_id.id,
                    }))

                    # Update market_value in investment_id based on conditions
                    if line.investment_id.market_value != 0:
                        new_market_value = current_market_rate
                    else:
                        new_market_value = current_market_rate
                    line.investment_id.write({'market_value': new_market_value})

                # Create the journal entry with accumulated amounts
                journal_entry = self.env['account.move'].create({
                    'journal_id': journal.id,  # Assuming 'journal' is defined somewhere in your code
                    'date': record.date,
                    'ref': record.name,
                    'line_ids': journal_lines,
                    'market_rate_id': record.id,
                })
                journal_entry.action_post()

            record.write({'state': 'posted'})
    def view_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.journal_entry_ids.ids)],
        }

    def action_cancel(self):
        for rec in self:
            print("mmkmknkjn")
            rec.write({'state':'cancel'})


class KgMarketRateLine(models.Model):
    _name='market.rate.line'

    market_rate_id = fields.Many2one('market.rate.updation')
    investment_id = fields.Many2one('kg.investment.entry',string='Investment Entry',required=True)
    available_shares = fields.Float(string='Available shares',required=True)
    face_value = fields.Float(string='Face Value',required=True,digits=(16, 6))
    market_rate = fields.Float(string='Market Rate',required=True,digits=(10,6))


