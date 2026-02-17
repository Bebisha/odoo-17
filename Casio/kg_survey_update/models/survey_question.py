from odoo import fields, models


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    update_result = fields.Boolean('Update Result on Contact', default=False)
    contact_field_id = fields.Many2one(
        'ir.model.fields',
        domain=[('model_id.model', '=', 'res.partner'), ('related', '=', False), ('readonly', '=', False),
                ('ttype', 'in', ['binary', 'char', 'date',
                  'datetime', 'float', 'html', 'integer',
                  'many2many', 'many2one', 'selection', 'text']),
                ('name', 'not in', ['calendar_last_notif_ack', 'channel_ids', 'agent_order', 'color', 'meeting_ids', 'message_bounce', 'meddage_partner_ids', 'signup_expiration', 'signup_token', 'signup_type', 'starred_message_ids'], )],
    )