# -*- coding: utf-8 -*-
import base64

from odoo import api, fields, models, _
import logging
import dateutil.parser

from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_allocation(self):
        payment_vals = []
        partner = False
        def_id = False
        company = False
        inv_vals = []
        for data in self:
            # if partner != data.partner_id.id and partner != False:
            #     raise ValidationError(_('Selected Payments are of different Partners'))

            # if data.is_reconciled:
            #     raise ValidationError(_('Already Reconciled'))

            val_1 = 0
            amount = 0
            partner = False
            debit = False
            credit = False
            move_id = False

            for line in self.line_ids:
                if line.partner_id:
                    partner = line.partner_id
                    debit = line.debit
                    credit = line.credit
                # else:
                #     partner = False

                # Exta condition added (inbound/outbound)
                if credit:
                    if line.debit == 0:
                        val_1 = line.id
                if debit:
                    if line.credit == 0:
                        val_1 = line.id

                val_1 = line.id
                amount += line.credit

            if credit:
                payment_type = 'inbound'
            else:
                payment_type = 'outbound'

            debit_id = self.env['account.partial.reconcile'].search([('credit_move_id', '=', val_1)])
            credit_id = self.env['account.partial.reconcile'].search([('debit_move_id', '=', val_1)])

            amount_bal = 0
            if credit:
                for val in debit_id:
                    amount_bal += val.debit_amount_currency
            elif debit:
                for val in credit_id:
                    amount_bal += val.credit_amount_currency

            payment_vals.append({
                'name': data.name,
                'date': data.date,
                'memo': data.ref,
                'move_line_id': val_1,
                'amount': amount if not debit else amount - amount_bal})

            def_id = data.id
            company = data.company_id.id

            invoice = self.search([('partner_id', '=', partner.id),
                                       ('payment_state', 'in', ['partial', 'not_paid', 'in_payment']),
                                       ('amount_residual', '!=', 0.0), ('state', '=', 'posted'),
                                       ('move_type','!=','entry')])

            for inv in invoice:
                val_2 = 0
                for line in inv.line_ids:
                    val_2 = line.id
                if inv.move_type == 'out_invoice':
                    if inv.line_ids.filtered(lambda l: l.credit == 0):
                        val_2 = inv.line_ids.filtered(lambda l: l.credit == 0)[0].id
                elif inv.move_type == 'in_invoice':
                    if inv.line_ids.filtered(lambda l: l.debit == 0):
                        val_2 = inv.line_ids.filtered(lambda l: l.debit == 0)[0].id
                inv_vals.append({'inv_amount': inv.amount_total,
                                 'name': inv.name,
                                 'inv_date': inv.invoice_date,
                                 'move_line_id': val_2,
                                 'date_due': inv.invoice_date_due,
                                 'inv_unallocated_amount': inv.amount_residual,

                                 })
            if amount - amount_bal == 0:
                raise ValidationError('Already Reconciled!!!')

        return {
            'name': 'Allocation',
            'res_model': 'payment.allocation.wizard',
            'type': 'ir.actions.act_window',
            'context': {'default_partner_id': partner,
                        # 'default_payment_id': def_id,
                        'default_payment_type': payment_type,
                        'default_balnc_paymnt_amnt': amount if not debit else amount - amount_bal,
                        'default_payment_allocation_ids': payment_vals,
                        'default_invoice_allocation_ids': inv_vals,
                        'default_company_id': company,

                        },
            'view_type': 'form',
            'view_mode': 'form,list',
            'target': 'new'}

