# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import base64
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_allocation(self):
        payment_vals = []
        inv_vals = []

        for data in self:
            # ---------------------------
            # Partner validation
            # ---------------------------
            partner = data.partner_id
            if not partner:
                raise ValidationError(_("Partner is missing on the payment."))

            company = data.company_id.id

            # ---------------------------
            # Find payment move line
            # ---------------------------
            payment_line = data.line_ids.filtered(
                lambda l: l.partner_id
                and not l.reconciled
                and l.account_id.account_type in ('asset_receivable', 'liability_payable')
            )[:1]

            if not payment_line:
                raise ValidationError(_("No valid payment line found for allocation."))

            # ---------------------------
            # Payment type & amount
            # ---------------------------
            payment_type = 'inbound' if payment_line.credit > 0 else 'outbound'
            amount = abs(payment_line.balance)

            # ---------------------------
            # Calculate already allocated amount
            # ---------------------------
            partials = self.env['account.partial.reconcile'].search([
                '|',
                ('debit_move_id', '=', payment_line.id),
                ('credit_move_id', '=', payment_line.id)
            ])

            allocated_amount = sum(
                abs(p.amount_currency) for p in partials
            )

            balance_amount = amount - allocated_amount

            if balance_amount <= 0:
                raise ValidationError(_("Already Reconciled !!!"))

            # ---------------------------
            # Payment values for wizard
            # ---------------------------
            payment_vals.append({
                'name': data.name,
                'date': data.date,
                'memo': data.ref,
                'move_line_id': payment_line.id,
                'amount': balance_amount,
            })

            # ---------------------------
            # Fetch open invoices
            # ---------------------------
            invoices = self.search([
                ('partner_id', '=', partner.id),
                ('payment_state', 'in', ['partial', 'not_paid', 'in_payment']),
                ('amount_residual', '>', 0),
                ('state', '=', 'posted'),
                ('move_type', '!=', 'entry'),
                ('company_id', '=', data.company_id.id),
            ])

            for inv in invoices:
                inv_line = inv.line_ids.filtered(
                    lambda l: l.partner_id
                    and l.account_id.account_type in ('asset_receivable', 'liability_payable')
                    and not l.reconciled
                )[:1]

                if not inv_line:
                    continue

                inv_vals.append({
                    'name': inv.name,
                    'inv_amount': inv.amount_total,
                    'inv_date': inv.invoice_date,
                    'date_due': inv.invoice_date_due,
                    'inv_unallocated_amount': inv.amount_residual,
                    'move_line_id': inv_line.id,
                })

        # ---------------------------
        # Open allocation wizard
        # ---------------------------
        return {
            'name': _('Allocation'),
            'res_model': 'payment.allocation.wizard',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': partner.id,
                'default_payment_type': payment_type,
                'default_balnc_paymnt_amnt': balance_amount,
                'default_payment_allocation_ids': payment_vals,
                'default_invoice_allocation_ids': inv_vals,
                'default_company_id': company,
            },
        }
