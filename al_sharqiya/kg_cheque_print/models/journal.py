# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    cheque_layout_id = fields.Many2one('kg.cheque.layout', string="Cheque Layout")


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    def action_print_cheque(self):
        if self.payment_method_line_id.code == 'check_printing':
            if not self.journal_id.cheque_layout_id:
                raise ValidationError(_('Please Configure Cheque Layout in journal !'))
            return self.env.ref('kg_cheque_print.kg_cheque_print_report').report_action(self)
        else:
            raise ValidationError(_('You can print only for check payment method !'))

    def get_reconciled_bills_list(self):
        invoices = self.reconciled_invoice_ids.mapped('name') if self.reconciled_invoice_ids else []
        bills = self.reconciled_bill_ids.mapped('name') if self.reconciled_bill_ids else []
        combined = invoices + bills
        return combined[:5]