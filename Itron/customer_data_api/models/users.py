from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    session_id = fields.Char('Session Id')
