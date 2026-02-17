# -*- coding: utf-8 -*-
# from odoo.exceptions import Warning

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, date


class kg_voucher(models.Model):
    _name = "kg.voucher"
    
    
    selectable_fields = ['kg_create_date','kg_valid_date','kg_customer_id','kg_disc_percent','kg_sales_person','state','name']

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(kg_voucher, self).fields_get(allfields, attributes=attributes) 
        not_selectable_fields = set(self._fields.keys()) - set(self.selectable_fields)
        for field in not_selectable_fields:
            if field in res:
                res[field]['selectable'] = False
        return res

    name = fields.Char('Name')
    kg_customer_id = fields.Many2one('res.partner', 'Customer')
    kg_valid_date = fields.Date('Validity Date', default=date.today() + timedelta(days=30))
    kg_create_date = fields.Date('Created Date', default=date.today())
    kg_disc_percent = fields.Float('Discount (%)', store=True,default=20.0)
    kg_sales_person = fields.Many2one('res.users', 'SalesPerson')
    state = fields.Selection([('new', 'New'), ('assign', 'Assigned'), ('redeem', 'Redeemed'), ('expire', 'Expired')],
                             'State', default='new')
    
    @api.model
    def create(self, vals):
        sequence_code = 'kg.voucher'
        v_code = self.env['ir.sequence'].next_by_code(sequence_code) or '/'
        vals['name'] = 'V/' + v_code
        return super(kg_voucher, self).create(vals)
