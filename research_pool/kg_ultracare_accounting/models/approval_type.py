
from odoo import models, fields, api, _


class ApprovalType(models.Model):
    _name = 'approval.type'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = 'Approval Type'

    name = fields.Char('Name')
    user_ids = fields.Many2many('res.users', 'approval_type_rel', string="Users")
