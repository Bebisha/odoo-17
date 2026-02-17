from odoo import models, fields, api


class BOMCategory(models.Model):
    _name = 'bom.category'

    name = fields.Char()
