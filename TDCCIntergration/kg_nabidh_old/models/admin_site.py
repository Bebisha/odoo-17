from odoo import models, fields, api, _



class KgAdminSite(models.Model):
    _name = 'admin.site'

    code = fields.Char(string="Value")
    name = fields.Char(string="Description")