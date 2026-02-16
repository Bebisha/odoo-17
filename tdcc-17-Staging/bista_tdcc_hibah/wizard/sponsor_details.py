# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
import warnings

from odoo.exceptions import UserError


class SponsorDetails(models.TransientModel):
    _name = "sponsor.details"
    _description = "Sponsor Details"

    sponsor_id = fields.Many2one("res.partner",string="Sponsor")
    percentage = fields.Float(string="Percentage")
    sponsor_amount = fields.Float(string="Sponsor Amount",
                                  compute="_compute_amount", store=True)
    invoice_amount = fields.Float(string="Invoice Amount")
    invoice_id = fields.Many2one("account.move",
                                 string="Invoice")
    available_balance = fields.Float(compute='compute_available_balance',
                                     string="Available Balance")


    @api.depends('sponsor_id')
    def compute_available_balance(self):
        if self.sponsor_id:
            debit = credit = 0.00
            journal_item_ids = self.env['account.move.line'].search([
                ('partner_id', '=', self.sponsor_id.id),
                ('account_id', '=', self.sponsor_id.account_sponsor_id.id)])
            for item in journal_item_ids:
                credit += item.credit
                debit += item.debit
            self.available_balance = credit - debit
        else:
            self.available_balance = 0.00
            pass

    @api.depends('percentage')
    def _compute_amount(self):
        self.ensure_one()
        self.sponsor_amount = (self.percentage * self.invoice_amount) / 100.0

    def add_sponsor_details(self):
        self.ensure_one()
        if self.percentage > 100.0:
            raise UserError(_("Percentage should not negative or more then 100"))
        self.invoice_id.write({
            'sponsor_id': self.sponsor_id.id,
            'percentage': self.percentage,
            'sponsor_amount': self.sponsor_amount,
        })
        return True
