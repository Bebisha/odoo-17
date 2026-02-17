from odoo import models, fields


class KGResUsersInherit(models.Model):
    _inherit = "res.users"

    inv_approval_limit = fields.Monetary(string="Invoice Approval Limit")
    bill_approval_limit = fields.Monetary(string="Bill Approval Limit")
