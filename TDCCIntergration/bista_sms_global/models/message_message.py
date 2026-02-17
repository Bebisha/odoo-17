# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from datetime import timedelta

from odoo import api, fields, models, _
import warnings
import requests
import logging
_logger = logging.getLogger(__name__)


class MessageMessage(models.Model):
    _name = 'message.message'
    _description = 'Message'

    @api.model
    def default_get(self, fields):
        res = super(MessageMessage, self).default_get(fields)
        sms_server_id = self.env['ir.sms_server'].search(
            [], order='sequence', limit=1)
        res.update(
            {'sms_server_id': sms_server_id and sms_server_id.id or False,
             'from_number': sms_server_id and sms_server_id.from_no})
        return res

    name = fields.Char(string="Subject", required=True)
    sms_template_id = fields.Many2one('sms.template', string='SMS template')
    from_number = fields.Char(string='From')
    to_number = fields.Char(string='To')
    partner_ids = fields.Many2many(
        'res.partner',
        'message_partner_rel',
     'message_id',
     'partner_id',
     string='Partner')
    model = fields.Char(string='Model', copy=False)
    message = fields.Text(string='Message')
    api_count = fields.Integer(string='API Call Count')
    sms_server_id = fields.Many2one('ir.sms_server', string='Server')
    message_id = fields.Char(string="SMSGlobalMsgID")
    author_id = fields.Many2one(
        'res.users',
        string="Author",
     default=lambda self: self.env.user.id)
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    state = fields.Selection([('draft', 'Outgoing'), ('exception', 'Failed'), (
        'sent', 'Sent'), ('cancel', 'Cancelled')], string='State', copy=False, default='draft')
    failure_reason = fields.Text(string='Comments', copy=False)
    res_id = fields.Integer(string="Related Document ID", copy=False)
    reply_to = fields.Char(string='Reply To')

    @api.onchange('sms_template_id')
    def onchange_template_id(self):
        if self.sms_template_id:
            self.sms_server_id = self.sms_template_id.sms_server_id or False
            self.from_number = self.sms_template_id.from_number
            self.name = self.sms_template_id.name
            self.model = self.sms_template_id.model_id.model

    @api.model
    def _cron_process_sms_queue(self):
        today = fields.Datetime.now()
        yesterday = today - timedelta(days=1)
        message_ids = self.search([('date', '>=', yesterday),
                                   ('state', '=', 'draft'),
                                   ('to_number', '!=', '')])
        for message_id in message_ids:
            try:
                message_id.action_send()
            except Exception:
                _logger.exception("Failed processing sms queue")
        return True

    @api.model
    def _cron_unlink_sent(self):
        unlink_message_ids = self.search([('state', '=', 'sent')])
        unlink_message_ids.unlink()

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_send(self):
        failed_numbers = []
        number_list = []
        next_to = ''
        from_number = self.from_number

        sms_server_id = self.sms_server_id
        if not sms_server_id:
            sms_server_id = self.env['ir.sms_server'].search(
                [], order='sequence', limit=1)
            if not sms_server_id:
                warnings.warn(
                    _('Please configure SMS server to process further!'))
            else:
                self.update({'sms_server_id': sms_server_id.id})

        if " " in self.from_number:
            from_number = self.from_number.replace(" ", "")
        if "+" in self.from_number:
            from_number = self.from_number.replace("+", "")
        if self.reply_to:
            message = self.message + '\n\n' + "To Reply -" + self.reply_to
        else:
            message = self.message

        send_sms_url = sms_server_id.send_sms_url


        if self.to_number and ',' in self.to_number:
            number_list = (self.to_number.split(','))
        else:
            number_list.append(str(self.to_number))
        for each_number in list(set(number_list)):
            if " " in each_number:
                each_number = each_number.replace(" ", "")
            if "+" in each_number:
                each_number = each_number.replace("+", "")
            params = '&user=' + sms_server_id.username + '&password=' + sms_server_id.password + \
                '&from=' + from_number + '&to=' + \
                each_number + '&text=' + message
            smsglobal_url = send_sms_url + params

            response = requests.get(url=smsglobal_url)
            self.write({'api_count' : self.api_count + 1})
            if "ERROR" in response.text:
                comment = "FAILED DELIVERY"
                failed_numbers.append(each_number)
            else:
                comment = "SUCCESSFULL"

        if comment != "SUCCESSFULL":
            failure_reason = response.text.split('ERROR:')
            if failed_numbers:
                for each_fail in list(set(failed_numbers)):
                    if len(failed_numbers) > 1:
                        next_to += str(each_fail) + ','
                    else:
                        next_to = str(each_fail)
            self.write(
                {'state': 'exception',
                 'to_number': next_to if next_to else '',
                 'message_id': False,
                 'failure_reason': failure_reason and failure_reason[1]})
        else:
            message_id = response.text.split('SMSGlobalMsgID:')
            self.write(
                {'state': 'sent',
                 'message_id': message_id and message_id[1],
                 'failure_reason': False})
        if self._context.get('from_retry'):
            self.write({'author_id': self.env.user.id})
        return True
