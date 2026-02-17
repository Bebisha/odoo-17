from odoo import api, models, _, fields


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    @api.model_create_multi
    def create(self, vals_list):
        company_currency = self.env.company.currency_id
        for vals in vals_list:
            if vals['foreign_currency_id']:
                currency = self.env['res.currency'].browse(vals['foreign_currency_id'])
                amount = currency._convert(vals['amount_currency'], company_currency, self.env.company,
                                           fields.Date.today())
                vals['amount'] = amount
        res = super(AccountBankStatementLine, self).create(vals_list)
        return res
