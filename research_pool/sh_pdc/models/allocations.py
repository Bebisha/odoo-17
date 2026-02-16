from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Allocations(models.Model):
    _inherit = 'advance.allocations'

    pdc_id = fields.Many2one('pdc.wizard')
    pdc_state = fields.Selection([('draft', 'Draft'), ('registered', 'Registered'), ('returned', 'Returned'),
                                  ('deposited', 'Deposited'), ('bounced', 'Bounced'), ('done', 'Done'),
                                  ('cancel', 'Cancelled')], string="State", related='pdc_id.state')
