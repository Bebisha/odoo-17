# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from markupsafe import Markup
from werkzeug.urls import url_join

from odoo import fields, models, _
from odoo.addons.sms.tools.sms_api import SmsApi
from odoo.addons.phone_validation.tools import phone_validation
import boto3
import os

class MassSMSTest(models.TransientModel):
    _inherit = 'mailing.sms.test'
    _description = 'Test SMS Mailing'

    def action_send_sms(self):
        self.ensure_one()

        numbers = [number.strip() for number in self.numbers.splitlines()]
        sanitized_numbers = [self.env.user._phone_format(number=number) for number in numbers]
        invalid_numbers = [number for sanitized, number in zip(sanitized_numbers, numbers) if not sanitized]

        record = self.env[self.mailing_id.mailing_model_real].search([], limit=1)
        body = self.mailing_id.body_plaintext
        if record:
            # Returns a proper error if there is a syntax error with qweb
            body = self.env['mail.render.mixin']._render_template(body, self.mailing_id.mailing_model_real, record.ids)[record.id]

        new_sms_messages_sudo = self.env['sms.sms'].sudo().create([{'mailing_id':self.mailing_id.id,'body': body, 'number': number} for number in sanitized_numbers])
        sms_api = SmsApi(self.env)
        sent_sms_list = sms_api._send_sms_batch([{
            'content': body,
            'numbers': [{'number': sms_id.number, 'uuid': sms_id.uuid} for sms_id in new_sms_messages_sudo],
        }], delivery_reports_url=url_join(self[0].get_base_url(), '/sms/status'))

        error_messages = {}
        if any(sent_sms.get('state') != 'success' for sent_sms in sent_sms_list):
            error_messages = sms_api._get_sms_api_error_messages()

        notification_messages = []
        if invalid_numbers:
            notification_messages.append(_('The following numbers are not correctly encoded: %s',
                ', '.join(invalid_numbers)))

        for sent_sms in sent_sms_list:
            if sent_sms.get('state') == 'success':
                notification_messages.append(
                    _('Test SMS successfully sent to %s', sent_sms.get('res_id')))
            elif sent_sms.get('state'):
                notification_messages.append(
                    _('Test SMS could not be sent to %s: %s',
                    sent_sms.get('res_id'),
                    error_messages.get(sent_sms['state'], _("An error occurred.")))
                )

        if notification_messages:
            message_body = Markup(
                f"<ul>{''.join('<li>%s</li>' for _ in notification_messages)}</ul>"
            ) % tuple(notification_messages)
            self.mailing_id._message_log(body=message_body)

        return True


    # def action_send_sms(self):
    #     self.ensure_one()
    #     numbers = [number.strip() for number in self.numbers.split(',')]
    #     sanitize_res = phone_validation.phone_sanitize_numbers_w_record(numbers, self.env.user)
    #     sanitized_numbers = [info['sanitized'] for info in sanitize_res.values() if info['sanitized']]
    #     invalid_numbers = [number for number, info in sanitize_res.items() if info['code']]
    #     if invalid_numbers:
    #         raise exceptions.UserError(_(
    #             'Following numbers are not correctly encoded: %s, example : "+32 495 85 85 77, +33 545 55 55 55"') % repr(
    #             invalid_numbers))

    #     message_attributes = {
    #         'CME_SMS_SVC': {
    #             'DataType': 'String',
    #             'StringValue': '635047399156',
    #         }
    #     }

        # sns = boto3.client('sns', region_name='ap-south-1', aws_access_key_id='AKIAZHW6GJ32OV3TELFE',
        #                    aws_secret_access_key='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')

        # for number in sanitized_numbers:
        #     sns.publish(
        #         PhoneNumber=number,
        #         Message=self.mailing_id.body_plaintext,
        #         MessageAttributes=message_attributes,
        #     )
        # return True
