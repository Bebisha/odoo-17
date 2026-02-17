from odoo import models, fields

class MailAlias(models.Model):
    _inherit = 'mail.alias'

    alias_user_id = fields.Many2one('res.users', string='Alias User')
