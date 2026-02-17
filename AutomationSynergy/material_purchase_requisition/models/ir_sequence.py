from odoo import api, fields, models, tools, _

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")