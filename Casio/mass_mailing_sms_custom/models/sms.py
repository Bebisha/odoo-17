# -*- coding: utf-8 -*-

import logging
from odoo import api, exceptions, fields, models, _
import boto3
from odoo.exceptions import UserError
import re
import werkzeug.urls


TEXT_URL_REGEX = r'https?://[a-zA-Z0-9@:%._+~#=/-]+'

_logger = logging.getLogger(__name__)

class Mailing(models.Model):
    _inherit = 'mailing.mailing'


    aws_topicarn = fields.Char(string='TopicArn')
    kg_message_id = fields.Char(string='MessageId')

    @api.model
    def create(self, vals):
        res = super(Mailing, self).create(vals)
        if res.mailing_type == 'sms':
            name = res.subject
            if ' ' in res.subject:
                name = res.subject.replace(" ","_")
            sns = boto3.client('sns', region_name='ap-south-1',aws_access_key_id='AKIAZHW6GJ32OV3TELFE',aws_secret_access_key='O8E/TSJGidN889fqJMWrPOcXSMA8cUlcu4sqRzkO')
            response = sns.create_topic(Name=name)
            res.aws_topicarn = response['TopicArn']
        return res


class SMSComposer(models.TransientModel):
    _inherit = 'sms.composer'

    def _get_unsubscribe_url(self, res_id, trace_code, number):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if self.env['ir.config_parameter'].sudo().get_param('web.base.alternative_url'):
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.alternative_url')
        return werkzeug.urls.url_join(
            base_url,
            '/sms/%s/%s' % (self.mailing_id.id, trace_code)
        )


class SMS(models.Model):
    _inherit = 'sms.sms'

    IAP_TO_SMS_STATE = {
        'success': 'sent',
        'insufficient_credit': 'sms_credit',
        'wrong_number_format': 'sms_number_format',
        'server_error': 'sms_server'
    }

    aws_subscriptionarn = fields.Char(string='SubscriptionArn')


    def _update_body_short_links(self):
        """ Override to tweak shortened URLs by adding statistics ids, allowing to
        find customer back once clicked. """
        shortened_schema = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + '/r/'
        if self.env['ir.config_parameter'].sudo().get_param('web.base.alternative_url'):
            shortened_schema = self.env['ir.config_parameter'].sudo().get_param('web.base.alternative_url') + '/r/'
        res = dict.fromkeys(self.ids, False)
        for sms in self:
            if not sms.mailing_id or not sms.body:
                res[sms.id] = sms.body
                continue

            body = sms.body
            for url in re.findall(TEXT_URL_REGEX, body):
                if url.startswith(shortened_schema):
                    body = body.replace(url, url + '/s/%s' % sms.id)
            res[sms.id] = body
        return res


    @api.model
    def create(self, vals):
        res = super(SMS, self).create(vals)
        if res.mailing_id and not res.mailing_id.aws_topicarn:
            raise UserError(('Topic is not generated in AWS server, Kindly check with your Administrator for this error!'))

        # _logger.debug('>>>>>>>>>>>>>>>>>',vals)
        # _logger.debug('>>>>>>>>>>>>>>>>>',res.number)
        sns = boto3.client('sns', region_name='ap-south-1',aws_access_key_id='AKIAZHW6GJ32OV3TELFE',aws_secret_access_key='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')

        response = sns.subscribe(TopicArn=res.mailing_id and str(res.mailing_id.aws_topicarn), Protocol="SMS", Endpoint=str(res.number or 0))
        # _logger.info('>>>>>>>>>>>>>>>>>')
        # _logger.info('>>>>>>>>>>>>>>>>>',res.number)
        res.aws_subscriptionarn = response['SubscriptionArn']
        return res

    def _send(self,unlink_failed=False, unlink_sent=True, raise_exception=False):
        """ This method tries to send SMS after checking the number (presence and
        formatting). """
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>___>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>)  )>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>| |>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>| |>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>| |>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>|___|>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        try:
            sns = boto3.client('sns', region_name='ap-south-1',aws_access_key_id='AKIAZHW6GJ32OV3TELFE',aws_secret_access_key='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')
            iap_results = sns.publish(TopicArn=self[0].mailing_id.aws_topicarn,Message=self[0].body)
            print(iap_results)
            self[0].mailing_id.kg_message_id = iap_results['MessageId']
        except Exception as e:
            _logger.info('Sent batch %s SMS: %s: failed with exception %s', len(self.ids), self.ids, e)
            if raise_exception:
                raise
            self._postprocess_iap_sent_sms([{'res_id': sms.id, 'state': 'server_error'} for sms in self], delete_all=unlink_failed)
        else:
            _logger.info('Send batch %s SMS: %s: gave %s', len(self.ids), self.ids, iap_results)
            self._postprocess_iap_sent_sms([{'res':res} for res in self], delete_all=unlink_failed)
        # return True

    def _postprocess_iap_sent_sms(self, iap_results, failure_reason=None, delete_all=False):
        if delete_all:
            todelete_sms_ids = [item.id for item in iap_results]
        else:
            todelete_sms_ids = [item['res'].id for item in iap_results if item['res'].state == 'sent']
        print(iap_results,'dddddddddddd')
        # for state in self.IAP_TO_SMS_STATE.keys():
        sms_ids = [item['res'].id for item in iap_results]
        if sms_ids:
            # if state != 'success' and not delete_all:
            self.env['sms.sms'].sudo().browse(sms_ids).write({
                'state': 'sent',
                # 'error_code': self.IAP_TO_SMS_STATE[state],
            })
            traces = self.env['mailing.trace'].sudo().search([('sms_id_int', 'in', sms_ids)])
            if traces:
                traces.write({'sent_datetime': fields.Datetime.now(), 'exception': False})
            # elif traces:
            #     traces.set_failed(failure_type=self.IAP_TO_SMS_STATE[state])

        if todelete_sms_ids:
            self.browse(todelete_sms_ids).sudo().unlink()