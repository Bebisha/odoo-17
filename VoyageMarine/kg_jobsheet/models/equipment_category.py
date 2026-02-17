
from odoo import models, fields


class KGEquipmentCatgeory(models.Model):
    _name = 'equipment.category'
    _description = 'Equipment Catgeory'

    name = fields.Char(string="Name")
    code = fields.Integer(string="Code")
    active = fields.Boolean(string="Active", default=True)