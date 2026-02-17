# -*- coding: utf-8 -*-
from pyfcm import FCMNotification
from odoo import models, fields


class PushNotification(models.Model):
    _name = 'push.notification'
    _rec_name = 'message_title'
    _description = "Push Notification"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one('res.users', string='User' ,readonly=True)
    device_id = fields.Char('Device ID',readonly=True)
    message_title = fields.Char('Message Title',readonly=True)
    message_body = fields.Text('Message Body',readonly=True)
    status = fields.Selection([('success', 'Success'),
                               ('failure', 'Failure')], default='failure')
    res_model_id = fields.Char('Res Model Id',readonly=True)
    res_model_name = fields.Char('Res Model Name',readonly=True)

    # def push_notification(self):
    #     """push notification: server action """
    #     active_line = self.env.user.login_ids.filtered(lambda x: x.is_active)
    #     for i in active_line:
    #         if i.device_id:
    #             api_key = self.env['ir.config_parameter'].sudo().get_param('kg_push_notification.api_key')
    #             push_service = FCMNotification(
    #                 api_key=api_key)
    #             registration_id = i.device_id
    #             message_title = "Push Notification device2"
    #             message_body = "Hello! Push notification Test"
    #             result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title,
    #                                                        message_body=message_body)
    #             if result:
    #                 if result['success'] == 1:
    #                     status = 'success'
    #                 else:
    #                     status = 'failure'
    #                 vals = {'user_id': self.env.user.id,
    #                         'device_id': i.device_id,
    #                         'message_title': message_title,
    #                         'message_body': message_body,
    #                         'status': status,
    #                         'res_model_id': i.id,
    #                         'res_model_name': 'login.details.line',
    #                         }
    #                 self.env['push.notification'].create(vals)

    # def send_push_notification(self, user_id=False, device_id=False, message_title=False, message_body=False,
    #                            res_model_id=False, res_model_name=False):
    #     """Common calling function to send push notification"""
    #     if device_id:
    #         api_key = self.env['ir.config_parameter'].sudo().get_param('kg_push_notification.api_key')
    #         push_service = FCMNotification(
    #             api_key=api_key)
    #         registration_id = device_id
    #         message_title = message_title
    #         message_body = message_body
    #         result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title,
    #                                                    message_body=message_body)
    #         if result:
    #             if result['success'] == 1:
    #                 status = 'success'
    #             else:
    #                 status = 'failure'
    #             vals = {'user_id': user_id,
    #                     'device_id': device_id,
    #                     'message_title': message_title,
    #                     'message_body': message_body,
    #                     'status': status,
    #                     'res_model_id': res_model_id,
    #                     'res_model_name': res_model_name,
    #                     }
    #             self.env['push.notification'].create(vals)
    #             return result
