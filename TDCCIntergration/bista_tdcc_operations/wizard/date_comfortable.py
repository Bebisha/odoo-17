# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
import warnings
from datetime import datetime
import pytz

from odoo.exceptions import UserError


class ClientDateComfortable(models.TransientModel):
    _name = 'client.date.comfortable'
    _description = 'Client Date Comfortable'

    line_ids = fields.One2many('client.date.comfortable.line',
                               'comfortable_id', string='Date Comfortable')

    def action_create_appointment_schedule(self):
        context = dict(self._context)
        active_id = context.get('active_id')
        active_model = self._context.get('active_model')
        group_booking_id = self.env[active_model].browse(active_id)
#         group_booking_id.appointment_ids.unlink()
        allowed_lines = self.line_ids.filtered(lambda l: l.allow)
        active_client_ids = context.get('client_ids')
        if all([not line.allow for line in allowed_lines]):
            raise UserError(_('Atleast one date is required to process.'))
        appointment_obj = self.env['appointment.appointment']
        for client in self.env['res.partner'].browse(active_client_ids):
            for line in allowed_lines:
                duration = line.end_time - line.start_time
                # Convert float to HH:MM format
                start_time = '{0:02.0f}:{1:02.0f}'.format(
                    *divmod(line.start_time * 60, 60))
                # Convert to time object
                start_time = datetime.strptime(start_time, '%H:%M').time()
                # Combine Date and Time
                start_dt = datetime.combine(line.date, start_time)
                # get User timezone
                user_tz = self.env.user.tz and \
                    pytz.timezone(self.env.user.tz) or pytz.utc
                # Convert Datetime to Datetime with timezone
                start_dt = user_tz.localize(start_dt)
                # Convert date from User timezone to UTC format
                start_dt = start_dt.astimezone(pytz.utc)
                start_date = start_dt.strftime(
                    '%Y-%m-%d %H:%M:%S')
                appointment_vals = {'client_id': client.id,
                                    'appointment_date': line.date,
                                    'start_date': start_date,
                                    'service_group_id':
                                    group_booking_id.service_group_id.id,
                                    'service_type_id':
                                    group_booking_id.service_type_id.id,
                                    'appointment_type_id':
                                    group_booking_id.appointment_type_id.id,
                                    'day': line.day,
                                    'start_time': line.start_time or 0.00,
                                    'end_time': line.end_time or 0.00,
                                    'group_appointment_booking_id':
                                    group_booking_id.id,
                                    'physician_id':
                                    group_booking_id.physician_id.id or False,
                                    'room_id':
                                    group_booking_id.room_id.id or False,
                                    'product_id':
                                    group_booking_id.product_id.id or False,
                                    'price_subtotal':
                                    group_booking_id.price_subtotal or 0.00,
                                    'duration': duration
                                    }
                appointment_obj.create(appointment_vals)
        group_booking_id.action_confirm()
        return True


class ClientDateComfortableLine(models.TransientModel):
    _name = 'client.date.comfortable.line'
    _description = 'Client Date Comfortable Line'

    comfortable_id = fields.Many2one(
        'client.date.comfortable',
        string='Date Comfortable')
    allow = fields.Boolean(string='Allow')
    date = fields.Date(string='Date')
    day = fields.Selection([('sun', 'Sunday'), ('mon', 'Monday'),
                            ('tue', 'Tuesday'), ('wed', 'Wednesday'),
                            ('thu', 'Thursday'), ('fri', 'Friday'),
                            ('sat', 'Saturday')], string='Schedule Days')
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
