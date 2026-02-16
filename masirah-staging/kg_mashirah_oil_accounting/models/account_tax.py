from odoo import models, fields, api, _


class AccountTax(models.Model):
    _inherit = 'account.tax'

    reverse_charge = fields.Boolean('Reverse Charge', copy=False)


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    active = fields.Boolean(default=True)
