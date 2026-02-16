from odoo import models, fields, api, _



class KgContactRole(models.Model):
    _name = 'contact.role'

    code = fields.Char(string="Code")
    name = fields.Char(string="Description")