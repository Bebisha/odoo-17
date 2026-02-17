from odoo import models, fields


class KGHRExpenseInherit(models.Model):
    _inherit = "hr.expense"

    is_select = fields.Boolean(default=False, string="Select")
