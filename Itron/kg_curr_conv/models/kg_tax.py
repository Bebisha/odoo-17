# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class AccountTax(models.Model):
    _inherit = "account.tax"

    is_tds = fields.Boolean('Is TDS',default=False)
    tds_account_id = fields.Many2one('account.account','TDS Account')