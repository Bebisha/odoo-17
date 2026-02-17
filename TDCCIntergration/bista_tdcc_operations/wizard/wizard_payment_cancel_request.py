# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api
from datetime import datetime


class CancelPaymentRequest(models.TransientModel):
    _name = 'wizard.cancel.payment.request'
    _description = 'Payment Cancel Request'

    name = fields.Text(string="Cancel Reason", required=True)


    def cancel_payment_request(self):
        context = dict(self.env.context)
        partner_obj = self.env['res.partner']
        mail_obj = self.env['mail.mail']
        if context.get('payment_id') and \
                context.get('active_model') == 'account.payment':
            cofounder_group_id = self.env.ref(
                'bista_tdcc_operations.group_tdcc_cofounder')
            payment_id = self.env['account.payment'].browse(
                context.get('payment_id'))
            payment_id.sudo().write({
                'cancel_reason': self.name,
                'payment_cancel_req_user_id': self.env.user.id,
                'payment_cancel_req_date': datetime.now(),
                'payment_cancel_req_sent': True})
            partner_ids = [user.partner_id.id
                           for user in cofounder_group_id.users]
            template_id = self.env.ref(
                'bista_tdcc_operations.payment_cancel_mail_template')
            template_id.send_mail(payment_id.id, force_send=True,
                                  email_values={'recipient_ids':
                                                [(6, 0, partner_ids)]})
        return True
