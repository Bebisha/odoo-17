from odoo import models, fields


class KGExpensePaymentWizard(models.TransientModel):
    """Multiple expense payment wizard."""

    _name = 'expense.payment.wizard'
    _description = 'Payment Wizard'

    payment_date = fields.Date('Payment Date',required=True, default=fields.Date.today,)
    expense_ids = fields.Many2many('hr.expense', string="Expenses")


    def action_paid(self):
        for rec in self.expense_ids:
            if rec.sheet_id:
               if  rec.sheet_id.state== 'approve':
                   rec.sheet_id.paid_on = self.payment_date
                   rec.sheet_id.action_paid()

