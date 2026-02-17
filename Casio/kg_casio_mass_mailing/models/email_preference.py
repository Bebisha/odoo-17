from odoo import api, fields, models


class EmailPreferences(models.Model):
    _name = 'email.preference'


    name = fields.Char(string='Name')
    email = fields.Char(string='Email')
    reason = fields.Many2one('unsubscribe.reason', string='Reason')
    frequency = fields.Many2one("email.preferences", string='Frequency')
    other_reason = fields.Char()

class EmailUnsubscri(models.Model):
    _name = 'unsubscribe.reasons'
    email = fields.Char(string='Email')
    reason = fields.Many2one('unsubscribe.reason', string='Reason')
    other_reason = fields.Char()