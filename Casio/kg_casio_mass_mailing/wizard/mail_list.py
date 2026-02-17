from odoo import api, fields, models
from ast import literal_eval

class EmailList(models.TransientModel):
    _name = 'email.list'

    line_ids = fields.One2many('email.list.line','list_id')

    def remove_from_mail_list(self):
        lines = []
        mail = self.env['mailing.mailing'].browse(self._context.get('active_ids', []))
        domain = literal_eval(mail.mailing_domain)
        lines = self.line_ids.filtered(lambda line: line.is_removed == True).mapped('object_id')
        domain.append(('id', 'not in',lines))
        mail.mailing_domain = repr(domain)


class EmailListLine(models.TransientModel):
    _name = 'email.list.line'


    list_id =  fields.Many2one('email.list')
    partner_id = fields.Many2one('res.partner',string="Customer")
    email = fields.Char()
    preference = fields.Many2one('email.preferences')
    fully_unsubscribed = fields.Char()
    total_email_sent = fields.Integer(string="Total email sent in last 30days")
    is_removed = fields.Boolean(default=False)
    object_id = fields.Integer()




