# -*- encoding: utf-8 -*-
from odoo import api, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def create(self, vals):
        """ function create supering to add the datas """
        context = self._context
        if context.get('email_cc'):
            vals['email_cc'] = context.get('email_cc')
        if context.get('email_to'):
            vals['email_to'] = context.get('email_to')
        res = super(MailMail, self).create(vals)
        if res.email_from:
            res.email_from = 'itron@klystronglobal.com'
        return res

    
