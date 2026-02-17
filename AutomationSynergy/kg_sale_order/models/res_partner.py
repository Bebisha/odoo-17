from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fax = fields.Char('Fax', copy=False)
    customer_type_id = fields.Many2one('res.customer.type', string='Customer Type')
