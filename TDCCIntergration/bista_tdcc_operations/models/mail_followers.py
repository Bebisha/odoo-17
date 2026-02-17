# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, api


class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    def _add_followers(self, res_model, res_ids, partner_ids, partner_subtypes,
                         check_existing=False,
                       existing_policy='skip'):
        # print("hhhhhhh",channel_ids)
        # print("ppppp",channel_subtypes)
        """
            Return empty dict for new and update followers by default,
            Return original value for followers when receiving context to add
            followers manually
        """
        new, update = super(MailFollowers, self.with_context(
            mail_create_nosubscribe=True))._add_followers(
                res_model, res_ids, partner_ids, partner_subtypes,
                 check_existing, existing_policy)
        if self._context.get('from_invite', False) or res_model == 'mail.channel':
            return new, update
        return {}, {}


class Invite(models.TransientModel):
    _inherit = 'mail.wizard.invite'


    def add_followers(self):
        # Added context to add followers manually
        return super(Invite, self.with_context(
            from_invite=True)).add_followers()


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    @api.model_create_multi
    def create(self, vals_list):
        # To prevent add default followers when create a record
        return super(MailThread, self.with_context(
            mail_create_nosubscribe=True)).create(
                vals_list)


    def _message_auto_subscribe_notify(self, partner_ids, template):
        return super(MailThread, self.with_context(
            mail_auto_subscribe_no_notify=True))._message_auto_subscribe_notify(
                partner_ids, template)
