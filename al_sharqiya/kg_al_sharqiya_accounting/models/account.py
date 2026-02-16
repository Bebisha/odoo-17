from odoo import models, api, fields, _


class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'

    is_trial_balance = fields.Boolean('Trial Balance')