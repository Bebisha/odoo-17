# -*- coding: utf-8 -*-
from odoo import fields, models, api,_
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit="purchase.order"

    partner_short_name = fields.Char('Partner Short Name', related='partner_id.name', store=True, readonly=True)
    
    local_curr_val = fields.Float('Local Currency Value',compute="convert_curr",store=True)
    company_currency_id = fields.Integer('Currency',compute="know_curr")
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Issued'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')
    invoice_status = fields.Selection([
        ('no', 'Paid'),
        ('to invoice', 'Waiting'),
        ('invoiced', 'Bills Received'),
    ], string='Billing Status', compute='_get_invoiced', store=True, readonly=True, copy=False, default='no')

    
    
    @api.depends('company_id')
    def know_curr(self):
        for record in self:
            currency=  record.env.user.company_id.currency_id
            record.company_currency_id =currency.id

    @api.depends('amount_total','currency_id')
    def convert_curr(self):
        for record in self:
            new_val=0.0
            ctx={}
            ctx['date'] = record.date_order
            if record.currency_id:
                new_val = record.currency_id._convert(record.amount_total,record.company_id.currency_id, record.company_id,
                                                           record.date_order)
            record.local_curr_val = new_val or 0.0
