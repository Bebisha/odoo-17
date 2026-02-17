# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    sponsor_id = fields.Many2one("res.partner", string="Sponsor",
                                 copy=False)
    percentage = fields.Float(string="Percentage", copy=False)
    sponsor_amount = fields.Float(string="Sponsor Amount", copy=False)
    is_hf = fields.Boolean(related="partner_id.is_hf")

    date = fields.Date(
        string='Date',
    )

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for rec in self:
            if rec.is_hf and rec.percentage and rec.sponsor_amount:
                if not rec.sponsor_id.account_sponsor_id:
                    raise ValidationError(_('Please add Sponsor Account on Sponsor form.'))
                receivable_line = rec.line_ids.filtered(lambda x: x.account_id.account_type == 'asset_receivable')
                if not receivable_line:
                    raise ValidationError(_('Receivable account line not found.'))
                if len(receivable_line) > 1:
                    raise ValidationError(_('Multiple receivable lines found. Please verify the journal entries.'))
                if receivable_line.debit < rec.sponsor_amount:
                    raise ValidationError(_('Sponsor amount cannot exceed the receivable amount.'))
                receivable_line.with_context(check_move_validity=False).write(
                    {'debit': receivable_line.debit - rec.sponsor_amount})
                sponsor_line_vals = {
                    'display_type': 'cogs',
                    'move_id': rec.id,
                    'partner_id': rec.sponsor_id.id,
                    'account_id': rec.sponsor_id.account_sponsor_id.id,
                    'debit': rec.sponsor_amount,
                    'credit': 0,
                    'name': 'Sponsor Hibah Fund',
                }
                rec.with_context(check_move_validity=False).write({'line_ids': [[0, 0, sponsor_line_vals]]})

        return res

    def sponsor_details_button(self):
        """
            - Open Sponsor wizard form view
        """
        percentage = 0
        service_type_ids = self.invoice_line_ids.mapped(
            'service_type_id').ids
        for service_type_id in self.partner_id.service_type_ids.ids:
            if service_type_id in service_type_ids:
                percentage = self.partner_id.hibah_percentage
        context = self._context.copy()
        context.update({'default_invoice_id': self.id,
                        'default_percentage': percentage,
                        'default_invoice_amount': self.amount_total,
                        })
        return {
            'name': 'Sponsor Form',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sponsor.details',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }
