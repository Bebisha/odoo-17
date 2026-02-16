# -*- coding: utf-8 -*-
from odoo import models, api,fields,_

class KGRevaluationJournal(models.Model):
    _name = 'kg.revaluation.journal'
    _description = 'Revaluation Journal'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Doc Id',copy=False,
                       readonly=True, index=True, default=lambda self: _('/'))
    company_id = fields.Many2one('res.company', string='Company', required=True)
    date = fields.Date(string='Date',default=fields.Date.today)
    currency_id = fields.Many2one('res.currency',string='Currency',required=True)
    journal_id = fields.Many2one('account.journal',string='Journal',required=True)
    exchange_rate = fields.Float(string='Exchange Rate',required=True)
    amount = fields.Monetary(string='Amount')
    reversible_transaction = fields.Boolean(string='Reversible Transaction')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
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
    reval_line_ids = fields.One2many('kg.revaluation.journal.line','revaluation_id')
    journal_entry_ids = fields.One2many('account.move', 'revaluation_id', string='Journal Entries')


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('revaluation.journal.seq')
        return super(KGRevaluationJournal, self).create(vals_list)

    def action_confirm(self):
        print("confirm")
        for rec in self:
            if rec.reval_line_ids:
                for record in rec.reval_line_ids:
                    print("record_credit=",record.credit)
                    print("record_debit=",record.debit)
                    journal_entry = self.env['account.move'].create({
                        'journal_id': rec.journal_id.id,
                        'date': rec.date,
                        'ref': rec.name,
                        'line_ids': [
                            (0, 0, {
                                'name': record.description,
                                'account_id': record.account_id.id,
                                'debit': record.debit,
                                'credit': 0.0,
                                'amount_currency': record.debit,
                                'currency_id': rec.currency_id.id,
                                # 'currency_rate':record.exchange_rate,

                            }),
                            (0, 0, {
                                'name': record.description,
                                'account_id': record.account_id.id,
                                'debit': 0.0,
                                'credit': record.credit,
                                'amount_currency': -record.credit,
                                'currency_id': rec.currency_id.id,
                                # 'currency_rate': record.exchange_rate,
                            }),
                        ],
                    })
                    journal_entry.write({'revaluation_id': rec.id})

                    journal_entry.action_post()
                rec.write({'state':'posted'})
    def view_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.journal_entry_ids.ids)],
        }

class KGRevaluationJournalLine(models.Model):
    _name = 'kg.revaluation.journal.line'

    revaluation_id = fields.Many2one('kg.revaluation.journal')
    account_id = fields.Many2one('account.account','Account')
    description = fields.Char(string='Description')
    debit = fields.Float(string='Debit')
    credit = fields.Float(string='Credit')

