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

    email_cc_ids = fields.Many2many('res.partner',"mail_message_res_partner_cc_rel",
        "mail_message_id",
        "parent_id", help="Carbon copy recipients", string="Cc")



    def action_send_mail(self):
        cc_emails = ','.join(partner.email for partner in self.email_cc_ids if partner.email)
        return self.with_context(email_cc=cc_emails)._action_send_mail()
