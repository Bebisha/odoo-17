# -*- coding: utf-8 -*-
from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    corresponding_bank_id = fields.Many2one('res.partner.bank', string='Corresponding Bank Account')
    need_invoice_approve = fields.Boolean(default=False,copy=False,string="Invoice Approve")
    need_bill_approve = fields.Boolean(default=False,copy=False,string="Bill Approve")
    company_seal = fields.Binary(string="Company Seal")

