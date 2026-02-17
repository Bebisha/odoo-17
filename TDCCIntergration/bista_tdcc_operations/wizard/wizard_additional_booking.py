# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
import warnings
import datetime
import pytz

from odoo.exceptions import UserError


class AdditionalBooking(models.TransientModel):
    _name = 'additional.booking'
    _description = 'Additional Booking'

    date_ids = fields.One2many('additional.booking.line', 'additional_id',
                               string='Dates', copy=False)


    def additional_booking(self):
        appointment_id = self._context.get('active_ids', [])[0]
        appointment = self.env[self._context.get(
            'active_model')].browse(appointment_id)
        for each in self.date_ids:
            if each.startdate:
                start_date = datetime.datetime.strptime(
                    str(each.startdate), '%Y-%m-%d %H:%M:%S')
                date_start = start_date.replace(tzinfo=pytz.utc).astimezone(
                    pytz.timezone(self.env.user.tz or 'UTC'))
                holiday_obj = self.env['public.holidays']
                is_public_holiday = holiday_obj.is_public_holiday(
                    str(date_start.date()))
                if is_public_holiday:
                    raise UserError(_("Clinic is off on %s scheduled date \
                         Please select another date!") % (
                             each.startdate.date()))
                new_apps = self.env['appointment.appointment'].create({
                    'name': self.env['ir.sequence'].next_by_code(
                        'appointment.appointment'),
                    'client_id': appointment.client_id.id or False,
                    'start_date': each.startdate,
                    'attendant_id':
                        appointment.attendant_id and appointment.attendant_id.id,
                    'duration': appointment.duration or 0.00,
                    'service_group_id': appointment.service_group_id.id or
                                         False,
                    'service_type_id':
                        appointment.service_type_id.id or False,
                    'appointment_type_id': appointment.appointment_type_id.id
                                        or False,
                    'clinic_id': appointment.clinic_id.id or False,
                    'physician_id': each.physician_id.id or
                                    appointment.physician_id.id or False,
                    'room_id': each.room_id.id or False,
                    'product_id': appointment.product_id.id or False,
                    'price_subtotal': appointment.price_subtotal or 0.00,
                    'state': 'confirmed'
                })


class AdditionalBookingLine(models.TransientModel):
    _name = 'additional.booking.line'
    _description = 'Additional Booking Line'

    additional_id = fields.Many2one('additional.booking',
                                    string='Additional Booking')
    date = fields.Datetime(string='Date')
    startdate = fields.Datetime(string='Start Date')
    room_id = fields.Many2one('room.room', string='Room')
    physician_id = fields.Many2one('res.partner',
                                   string='Physician',
                                   domain=[('is_physician', '=', True)])

    @api.model
    def default_get(self, fields_lst):
        res = super(AdditionalBookingLine, self).default_get(fields_lst)
        appointment_id = self._context.get('active_ids', [])[0]
        appointment = self.env[self._context.get(
            'active_model')].browse(appointment_id)
        res.update(physician_id=appointment.physician_id.id or False)
        res.update(room_id=appointment.room_id.id or False)
        return res
