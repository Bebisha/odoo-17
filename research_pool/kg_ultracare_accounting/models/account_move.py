# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import json

from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def get_default_purchase_order(self):
        purchase_id = self.env['purchase.order'].search([])
        if purchase_id:
            list = []
            for i in purchase_id:
                list.append(i.id)
            return list

    @api.onchange('partner_id')
    def add_customer_rank_domain(self):
        if self.move_type == 'out_invoice':
            customer = []
            partner_id = self.env['res.partner'].search([])
            for res in partner_id:
                if res.customer_rank > 0:
                    customer.append(res.id)
            return {
                'domain': {
                    'partner_id': [
                        ('id', 'in', customer)
                    ]
                }
            }

    purchase_order_ids = fields.Many2many('purchase.order', default=get_default_purchase_order, string='Purchase Order',
                                          store=True)
    purchase_vendor_bill_id = fields.Many2one('purchase.bill.union',
                                              states={'draft': [('readonly', False)]},
                                              string='Auto-complete',
                                              domain="[('purchase_order_id', 'in', purchase_order_ids),('partner_id','=',partner_id)]",
                                              help="Auto-complete from a past bill / purchase order.")
    first_label = fields.Char(string="First Label")

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        if self.purchase_vendor_bill_id:
            self.invoice_line_ids = False
            return super(AccountMove, self)._onchange_purchase_auto_complete()

    @api.constrains('ref')
    def constraints_ref(self):
        if not self.ref and self.move_type == 'in_invoice':
            raise UserError('Please Add Bill Reference and Continue!')

    @api.onchange('ref')
    def check_bill_ref(self):
        for rec in self:
            if rec.move_type == 'in_invoice':
                if rec.ref:
                    bill_id = self.env['account.move'].search([('ref', '=', rec.ref)], limit=1)
                    if bill_id:
                        raise ValidationError("This bill reference has been already used for %s" % (bill_id.name))

    @api.onchange('line_ids')
    def get_label(self):
        for rec in self:
            if rec.journal_id.name == 'Miscellaneous Operations' and rec.line_ids and rec.move_type == 'entry':
                for line in rec.line_ids:
                    if line.name:
                        rec.first_label = line.name
                        return
                rec.first_label = False
            else:
                rec.first_label = False


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_reconciled = fields.Boolean('Reconciled')
    analytic_distribution_amount = fields.Json("Analytic Amount")

    @api.onchange('account_id')
    def get_label(self):
        for rec in self:
            if rec.move_id.first_label:
                rec.name = rec.move_id.first_label
