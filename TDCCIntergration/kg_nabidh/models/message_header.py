from odoo import fields, models, api,_



class KgMessageHeader(models.Model):
    _name = 'message.headers'


    message_header_id = fields.Many2one('res.partner', string='Student')