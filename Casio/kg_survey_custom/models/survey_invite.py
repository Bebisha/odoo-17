from odoo import api, fields, models, tools


class SurveyInviteInherited(models.TransientModel):
    _inherit = 'survey.invite'

    email_from = fields.Char('From', help="Email address of the sender.")
    email_from_id = fields.Many2one('email.from', string='From')

    @api.onchange('email_from_id')
    def onchange_email_from_id(self):
        if self.email_from_id:
            self.email_from = tools.formataddr((self.email_from_id.name, self.email_from_id.email))


class EmailFrom(models.Model):
    _name = 'email.from'

    name = fields.Char('Name',required=True)
    email = fields.Char('Email',required=True)
