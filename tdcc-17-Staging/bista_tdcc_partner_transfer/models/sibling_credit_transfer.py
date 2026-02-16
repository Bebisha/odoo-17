# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class StudentCreditTransder(models.Model):
    _name = 'student.credit.transfer'
    _description = 'Transfer amount between siblings'
    _order = 'name desc'

    @api.depends('from_partner_id')
    def compute_advance_amount(self):
        if not self.from_partner_id:
            self.advance_amount = 0.00
        if self.from_partner_id.total_due < 0:
            self.advance_amount = abs(self.from_partner_id.total_due) or 0.00
        else:
            self.advance_amount = 0

    name = fields.Char(string="Name", required=True, copy=False, default='/')
    from_partner_id = fields.Many2one('res.partner', string="From Student",
                                      required=True)
    to_partner_id = fields.Many2one('res.partner', string="To Student",
                                    required=True)
    advance_amount = fields.Float(string="Advance Amount",
                                  compute=compute_advance_amount)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id.id)
    transfer_amount = fields.Float(string="Transfer Amount", copy=False)
    state = fields.Selection([('draft', 'draft'),
                              ('submit', 'submitted'),
                              ('approve', 'Approved'),
                              ('reject', 'Rejected'),
                              ('cancel', 'Cancelled'),
                              ('done', 'Done')],
                             default='draft', string="Status")
    clinic_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id.id)
    approval_date = fields.Date(string="Approval Date", copy=False)
    transaction_date = fields.Date(string="Transaction Date", copy=False)

    # @api.multi
    def button_journal_entries(self):
        return {
            'name': _('Journal Items'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('ref', 'ilike', self.name)],
        }

    @api.constrains('transfer_amount')
    def _check_transfer_amount(self):
        for each in self:
            if each.transfer_amount <= 0:
                raise ValidationError(_(
                    'The transfer amount should be positive.'))
            if each.transfer_amount > each.advance_amount:
                raise ValidationError(_(
                    '%s has only %s %s credit to transfer.'
                    % (each.from_partner_id.name, each.advance_amount,
                       each.currency_id.name)))

    def action_create_move_line(self, move_ids):
        transfer_acc_id = int(self.env['ir.config_parameter'].sudo(
        ).get_param('transfer_account_id'))
        if not transfer_acc_id:
            transfer_acc_id = self.env.user.company_id.transfer_account_id.id,
        line = False
        credit_aml_dict = debit_aml_dict = {}
        currency_id = self.env.user.company_id.currency_id
        to_acc_id = self.to_partner_id.property_account_receivable_id
        from_acc_id = self.from_partner_id.property_account_receivable_id
        for move in move_ids:
            if line:
                credit_aml_dict = {'name': _('Transfer from %s')
                                   % self.from_partner_id.name,
                                   'partner_id': self.to_partner_id.id,
                                   'move_id': move.id,
                                   'debit': 0.00,
                                   'amount_currency': -self.transfer_amount,
                                   'credit': self.transfer_amount,
                                   'account_id': to_acc_id.id,
                                   'journal_id': move.journal_id.id,
                                   'currency_id': currency_id.id}
                debit_aml_dict = {'name': _('Transfer To %s') %
                                  self.to_partner_id.name,
                                  'move_id': move.id,
                                  'debit': self.transfer_amount,
                                  'amount_currency': self.transfer_amount,
                                  'credit': 0.00,
                                  'account_id': transfer_acc_id,
                                  'journal_id': move.journal_id.id,
                                  'currency_id': currency_id.id}
            else:
                credit_aml_dict = {
                    'name': _('Transfer from %s') % self.from_partner_id.name,
                    'move_id': move.id,
                    'debit': 0.00,
                    'credit': self.transfer_amount,
                    'account_id': transfer_acc_id,
                    'journal_id': move.journal_id.id,
                    'currency_id': currency_id.id}

                debit_aml_dict = {
                    'name': _('Transfer To %s') % self.to_partner_id.name,
                    'partner_id': self.from_partner_id.id,
                    'move_id': move.id,
                    'debit': self.transfer_amount,
                    'credit': 0.00,
                    'account_id': from_acc_id.id,
                    'journal_id': move.journal_id.id,
                    'currency_id': currency_id.id}
                line = True
            move.update(
                {'line_ids': [(0, 0, credit_aml_dict),
                              (0, 0, debit_aml_dict)]})
            # Check if only posted payments to take?
            payment_ids = self.env['account.payment'].search([
                ('partner_id', '=', self.from_partner_id.id),
                ('state', '=', 'posted'),
                ('payment_type', '=', 'inbound')])
            lines_to_reconcile = self.env['account.move.line']
            for payment_id in payment_ids:
                lines_to_reconcile += payment_id.move_line_ids.filtered(
                    lambda r: not r.reconciled and
                    r.account_id.internal_type == 'receivable')
            if lines_to_reconcile:
                debit_aml_id = self.env['account.move.line'].search(
                    [('move_id', '=', move.id),
                     ('debit', '>', 0),
                     ('partner_id', '=', self.from_partner_id.id),
                     ('account_id.internal_type', '=', 'receivable')])

                lines_to_reconcile += debit_aml_id
                lines_to_reconcile.reconcile()
        return True

    def action_create_move(self):
        journal = self.env[
            'account.journal'].search([('type', '=', 'general')],
                                      limit=1)
        if not journal:
            raise UserError(_(
                "Unable to transfer amount, please configure the sale journal."
            ))
        vals_list = [{'date': fields.date.today(),
                      'ref': self.name or '',
                      'company_id': self.clinic_id.id,
                      'journal_id': journal.id},
                     {'date': fields.date.today(),
                      'ref': self.name or '',
                      'company_id': self.clinic_id.id,
                      'journal_id': journal.id, }]
        move_ids = self.env['account.move'].create(vals_list)
        self.action_create_move_line(move_ids)
        move_ids.action_post()
        return move_ids

    # @api.multi
    def action_submit(self):
        self.ensure_one()
        return self.update({'state': 'submit'})

    # @api.multi
    def action_cancel(self):
        self.ensure_one()
        return self.update({'state': 'cancel'})

    # @api.multi
    def action_approve(self):
        self.ensure_one()
        return self.update({'state': 'approve',
                            'approval_date': fields.date.today()})

    # @api.multi
    def action_create_journal_entry(self):
        self.ensure_one()
        self.action_create_move()
        self.update({'state': 'done',
                     'transaction_date': fields.date.today()})
        return True

    # @api.multi
    def action_reject(self):
        self.ensure_one()
        return self.update({'state': 'reject'})

    @api.onchange('from_partner_id')
    def onchange_from_partner_id(self):
        if not self.from_partner_id or not self.from_partner_id.sibling_ids:
            self.to_partner_id = False
        return {'domain': {'to_partner_id': [
            ('id', 'in', self.from_partner_id.sibling_ids.ids)]}}

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'student.credit.transfer')
        return super(StudentCreditTransder, self).create(vals)
