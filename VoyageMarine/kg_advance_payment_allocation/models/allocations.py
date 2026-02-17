from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Allocations(models.Model):
    _name = 'advance.allocations'

    type = fields.Selection([('payment','payment'),('pdc','pdc')])
    amount = fields.Float()
    payment_id = fields.Many2one('account.payment')
    payment_state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'),('cancel', 'Cancelled')], string="State", related='payment_id.state')
    invoice_id = fields.Many2one('account.move')



