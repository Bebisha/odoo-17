from odoo import models, fields


class InheritAccountPayment(models.Model):

    _inherit = "account.payment"
