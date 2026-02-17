
from odoo import models, fields


class KGEquipmentMaster(models.Model):
    _name = 'equipment.master'
    _description = 'Equipment Master'

    name = fields.Char(string="Equipment")
    code = fields.Integer(string="Code")
    active = fields.Boolean(string="Active", default=True)
    equipment_category = fields.Many2one('equipment.category',string="Equipment Category")








