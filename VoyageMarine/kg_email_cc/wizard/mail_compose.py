# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models


class MailMail(models.TransientModel):
    _inherit = 'mail.compose.message'

    email_cc = fields.Char('Cc', help="Carbon copy recipients")
    email_cc_ids = fields.Many2many('res.partner', "mail_message_res_partner_cc_rel",
                                    "mail_message_id",
                                    "parent_id", help="Carbon copy recipients", string="Cc")

    def _action_send_mail(self, auto_commit=False):
        cc_emails = ','.join(partner.email for partner in self.email_cc_ids if partner.email)
        self = self.with_context(email_cc=cc_emails)
        return super(MailMail, self)._action_send_mail(auto_commit=auto_commit)

    def action_send_mail(self):
        cc_emails = ','.join(partner.email for partner in self.email_cc_ids if partner.email)
        return self.with_context(email_cc=cc_emails)._action_send_mail()
