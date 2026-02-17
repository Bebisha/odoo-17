# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools import float_compare


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    communication = fields.Char(string="Communication", compute="compute_communication")

    @api.onchange('product_id')
    def _onchange_product_id_set_analytic(self):
        if self.move_id and self.move_id.kg_analytic_account_id:
            self.analytic_distribution = {str(self.move_id.kg_analytic_account_id.id): 100}
        else:
            self.analytic_distribution = {}

    def compute_communication(self):
        for rec in self:
            rec.communication = False
            if rec.ref:
                rec.communication = f"{rec.ref} - {rec.name}"
            else:
                rec.communication = rec.name

    def _convert_to_tax_base_line_dict(self):
        res = super(AccountMoveLine, self)._convert_to_tax_base_line_dict()
        is_invoice = self.move_id.is_invoice(include_receipts=True)
        if is_invoice:
            if self.sale_line_ids:
                quantity = self.weight
            else:
                quantity = self.quantity
        else:
            quantity = 1.0
        res['quantity'] = quantity
        return res

    def _prepare_analytic_lines(self):
        self.ensure_one()
        analytic_line_vals = []

        if self.analytic_distribution:
            # Stores distribution for each plan to give accurate amounts when 100% distribution is achieved
            distribution_on_each_plan = {}

            for account_ids, distribution in self.analytic_distribution.items():
                # Recursively prepare lines for the account and its parents
                self._prepare_lines_for_account_and_parents(
                    account_ids, distribution, distribution_on_each_plan, analytic_line_vals
                )

        return analytic_line_vals

    def _prepare_lines_for_account_and_parents(self, account_ids, distribution, distribution_on_each_plan,
                                               analytic_line_vals):
        """
        Recursively prepare analytic distribution lines for the account and its parents.
        """
        account_id = int(account_ids)
        account = self.env['account.analytic.account'].browse(account_id)

        while account:
            line_values = self._prepare_analytic_distribution_line(
                float(distribution), account.id, distribution_on_each_plan
            )

            # Add line only if the amount is non-zero
            if not self.currency_id.is_zero(line_values.get('amount')):
                analytic_line_vals.append(line_values)

            account = account.parent_id if account.parent_id else None

    def _prepare_analytic_distribution_line(self, distribution, account_ids, distribution_on_each_plan):
        """ Prepare the values used to create() an account.analytic.line upon validation. """
        self.ensure_one()
        account_field_values = {}
        decimal_precision = self.env['decimal.precision'].precision_get('Percentage Analytic')
        amount = 0

        account_ids = [account_ids] if isinstance(account_ids, int) else account_ids

        for account in self.env['account.analytic.account'].browse(account_ids).exists():
            distribution_plan = distribution_on_each_plan.get(account.root_plan_id, 0) + distribution
            if float_compare(distribution_plan, 100, precision_digits=decimal_precision) == 0:
                amount = -self.balance * (100 - distribution_on_each_plan.get(account.root_plan_id, 0)) / 100.0
            else:
                amount = -self.balance * distribution / 100.0
            distribution_on_each_plan[account.root_plan_id] = distribution_plan
            account_field_values[account.plan_id._column_name()] = account.id

        default_name = self.name or (self.ref or '/' + ' -- ' + (self.partner_id.name if self.partner_id else '/'))
        return {
            'name': default_name,
            'date': self.date,
            **account_field_values,
            'partner_id': self.partner_id.id,
            'unit_amount': self.quantity,
            'product_id': self.product_id.id if self.product_id else False,
            'product_uom_id': self.product_uom_id.id if self.product_uom_id else False,
            'amount': amount,
            'general_account_id': self.account_id.id,
            'ref': self.ref,
            'move_line_id': self.id,
            'user_id': self.move_id.invoice_user_id.id or self._uid,
            'company_id': self.company_id.id or self.env.company.id,
            'category': 'invoice' if self.move_id.is_sale_document() else 'vendor_bill' if self.move_id.is_purchase_document() else 'other',
        }
