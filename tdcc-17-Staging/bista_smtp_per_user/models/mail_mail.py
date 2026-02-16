# -*- coding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api
from odoo.addons.base.models.ir_mail_server import extract_rfc2822_addresses


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    user_id = fields.Many2one('res.users', string='Owner')
    smtp_user = fields.Char(string='Username',
                            help="Optional username for SMTP authentication",
                            groups="")
    smtp_pass = fields.Char(string='Password',
                            help="Optional password for SMTP authentication",
                            groups="")

    _sql_constraints = [
        ('smtp_user_uniq', 'unique(user_id)',
         'That user already has a SMTP server.')
    ]

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if not self.user_id:
            return
        self.smtp_user = self.user_id.login

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None,
                   smtp_port=None, smtp_user=None, smtp_password=None,
                   smtp_encryption=None, smtp_debug=False,
                   smtp_session=None):
        from_rfc2822 = extract_rfc2822_addresses(message['From'])[-1]
        server_id = self.env['ir.mail_server'].search([
            ('smtp_user', '=', from_rfc2822)])
        if server_id and server_id[0]:
            message['Return-Path'] = from_rfc2822
        return super(IrMailServer, self).send_email(
            message, mail_server_id, smtp_server, smtp_port, smtp_user,
            smtp_password, smtp_encryption, smtp_debug, smtp_session)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    # @api.multi
    def send(self, auto_commit=False, raise_exception=False):
        for email in self:
            # from_rfc2822 = extract_rfc2822_addresses(email.email_from)[-1]
            # <----code changed by Klystron Global,just removed the limit,by shaniba klystron--->
            from_rfc2822 = extract_rfc2822_addresses(email.email_from)
            server_id = self.env['ir.mail_server'].search([
                ('smtp_user', '=', from_rfc2822)])
            server_id = server_id and server_id[0] or False
            if server_id:
                self.write({'mail_server_id': server_id[0].id,
                            'reply_to': email.email_from})
        return super(MailMail, self).send(auto_commit=auto_commit,
                                          raise_exception=raise_exception)
