# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
import datetime
import pytz
from odoo.exceptions import UserError


class RescheduleAppointment(models.TransientModel):
    _name = 'reschedule.appointment'
    _description = 'Rearrange Appointment'

    reschedule_reason = fields.Many2one('appointment.rearrange.reason',
                                        string="Rearrange Reason", required=True)
    start_date = fields.Datetime(string='Start Date', copy=False)
    end_date = fields.Date(string='End Date', copy=False)
    day_ids = fields.Many2many('week.days', string="Comfort Days")
    appointment_type_id = fields.Many2one(
        'appointment.type', string="Appointment Type")
    room_id = fields.Many2one('room.room', string="Room")
    physician_id = fields.Many2one('res.partner', domain=[
        ('is_physician', '=', True)])
    duration = fields.Float(string="Duration", copy=False)
    product_id = fields.Many2one('product.product', string='Price List')
    price_subtotal = fields.Float(
        string='Amount',
        digits=dp.get_precision('Account'))
    rearrange_child_appointment = fields.Boolean(
        string="Rearrange Child Appointment")
    clinic_id = fields.Many2one('res.company',
                                string="Clinic",
                                copy=False,
                                default=lambda self: self.env[
                                    'res.company']._company_default_get())
    group_appointment_booking_id = fields.Many2one('group.appointment.booking')
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')
    day = fields.Selection([('sun', 'Sunday'), ('mon', 'Monday'),
                            ('tue', 'Tuesday'), ('wed', 'Wednesday'),
                            ('thu', 'Thursday'), ('fri', 'Friday'),
                            ('sat', 'Saturday')], string='Day')
    appointment_date = fields.Date(string="Appointment Date")

    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.start_date:
            holiday_obj = self.env['public.holidays'].search([
                ('date', '=', self.start_date.date()),
                ('clinic_id', '=', self.clinic_id.id)
            ])
            if not holiday_obj:
                holiday_obj = self.env['public.holidays'].search([
                    ('date', '=', self.start_date.date()),
                    ('clinic_id', '=', False)
                ])
            if holiday_obj:
                raise UserError(_("Clinic is off on this scheduled date!"))

            if self.end_date and self.start_date.date() > self.end_date:
                raise UserError(_("Start date cannot be greater than end date!"))

    @api.onchange('appointment_date')
    def onchange_appointment_date(self):
        if self.appointment_date:
            try:
                day = self.appointment_date.strftime('%a').lower()
                self.day = day
            except Exception as e:
                raise UserError(_("Error while processing the appointment date: %s") % str(e))

    @api.onchange('start_time', 'end_time')
    def onchange_appointment_time(self):
        if self.start_time and self.end_time:
            if self.start_time > self.end_time:
                raise UserError(_("Start time cannot be later than end time!"))
            self.duration = self.end_time - self.start_time

    @api.onchange('appointment_type_id')
    def onchange_appointmenyt_type(self):
        if self.appointment_type_id:
            self.product_id = self.appointment_type_id.product_id
            self.price_subtotal = self.appointment_type_id.price
        else:
            self.product_id = False
            self.price_subtotal = 0.00

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            self.price_subtotal = 0.00
        else:
            self.price_subtotal = self.product_id.lst_price or 0.00

    @api.model
    def default_get(self, fields):
        res = super(RescheduleAppointment, self).default_get(fields)
        if self._context is None:
            self._context = {}
            return {}

        appointment_id = self._context.get('active_ids', [])[0]
        appointment_id_obj = self.env[self._context.get(
            'active_model')].browse(appointment_id)
        res['start_date'] = appointment_id_obj.start_date or False
        res['end_date'] = appointment_id_obj.end_date or False
        res['day_ids'] = [(6, 0, appointment_id_obj.week_days_ids.ids)] or False
        res['appointment_type_id'] = appointment_id_obj. \
                                         appointment_type_id.id or False
        res['room_id'] = appointment_id_obj.room_id.id or False
        res['physician_id'] = appointment_id_obj.physician_id.id or False
        res['duration'] = appointment_id_obj.duration or False
        res['product_id'] = appointment_id_obj.product_id.id or False
        res['price_subtotal'] = appointment_id_obj.price_subtotal or False
        res['clinic_id'] = appointment_id_obj.clinic_id.id or False
        if appointment_id_obj.group_appointment_booking_id:
            res['group_appointment_booking_id'] = \
                appointment_id_obj.group_appointment_booking_id.id
            res['start_time'] = appointment_id_obj.start_time
            res['end_time'] = appointment_id_obj.end_time
            res['day'] = appointment_id_obj.day
            res['appointment_date'] = appointment_id_obj.appointment_date
        return res

    def action_rearrange_appointment(self):
        """
        Reschedule Appointment and child appointments
        """
        appo_env = self.env['appointment.appointment']
        if self._context.get('active_id', False):
            appo = appo_env.browse(self._context.get('active_id'))
            if not appo.end_date and self.end_date:
                raise UserError(_('You can not Add End Date from here.'))

            # Restrict rearrange if new start date is past date
            if appo.start_date.date() > fields.Date.today(
            ) and self.start_date.date() < fields.Date.today():
                raise UserError(_("Start date can not be a past date !"))
            start_date = appo.start_date
            end_date = appo.end_date
            days_ids = appo.week_days_ids.ids
            # Rearrange main appointment
            if appo and appo.state != 'cancelled':
                if not appo.group_appointment_booking_id:
                    main_appointment = True
                else:
                    main_appointment = False
                self.with_context({'main_appointment': main_appointment}) \
                    .set_appointment_value(appo)
            # Rearrange child appointmentgroup_appointment_booking_id
            if self.rearrange_child_appointment and appo \
                    .appointment_line_ids:
                # Check if days are same and start or end date is different
                if self.day_ids and days_ids == self.day_ids.ids and (
                        (appo.start_date != start_date) or
                        (appo.end_date != end_date)):
                    for appointment in appo.appointment_line_ids:
                        if (appointment.start_date and
                            appointment.start_date <
                            appo.start_date) or (
                                appointment.start_date and
                                appointment.start_date.date() >
                                appo.end_date):
                            if appointment.start_date.date() > \
                                    fields.Date.today():
                                appointment.write({'state': 'cancelled'})
                        else:
                            if appointment.state != 'cancelled':
                                self.set_appointment_value(appointment)
                    appo.generate_comfort_days()
                elif self.day_ids and days_ids != self.day_ids.ids:
                    for appointment in appo.appointment_line_ids:
                        appointment.write({'state': 'cancelled'})
                    appo.generate_comfort_days()
                else:
                    for appointment in appo.appointment_line_ids:
                        if appointment.state != 'cancelled':
                            self.set_appointment_value(appointment)
        return {'type': 'ir.actions.act_window_close'}

    def set_appointment_value(self, appointment):
        d1 = datetime.datetime.strptime(
            str(appointment.start_date), '%Y-%m-%d %H:%M:%S')
        d1 = d1.replace(
            tzinfo=pytz.utc).astimezone(
            pytz.timezone(
                self.env.user.tz or 'UTC'))
        d2 = d1 + datetime.timedelta(hours=appointment.duration)
        if appointment.group_appointment_booking_id:
            start_date = appointment.appointment_date
            start_time = appointment.start_time
            end_time = appointment.end_time
        else:
            start_date = datetime.datetime.strptime(
                str(appointment.start_date)[:10], '%Y-%m-%d').date()
            start_time = "%s.%s" % (str(d1.hour),
                                    str(d1.minute * 1666666667)) or 0.00
            end_time = "%s.%s" % (str(d2.hour),
                                  str(d2.minute * 1666666667)) or 0.00
        values = {
            'appointment_id': appointment.id or False,
            'group_appointment_booking_id':
                appointment.group_appointment_booking_id.id or False,
            'appointment_type_id':
                appointment.appointment_type_id.id or False,
            'room_id': appointment.room_id.id or False,
            'client_id': appointment.client_id.id or False,
            'duration': appointment.duration or False,
            'start_date': start_date,
            'rearrange_id': self.reschedule_reason.id or False,
            'day_ids': [(6, 0, appointment.week_days_ids.ids if not
            self.group_appointment_booking_id else [])],
            'appointment_week_day': appointment.day if
            self.group_appointment_booking_id else '',
            'start_time': start_time,
            'end_time': end_time,
            'write_by_id': self._uid or self._uid.id,
            'physician_id':
                appointment.physician_id.id or False,
            'product_id': appointment.product_id.id or False,
            'price_subtotal':
                appointment.price_subtotal or False,
        }
        if appointment.end_date:
            values.update(
                {'end_date': datetime.datetime.
                strptime(str(appointment.end_date)[:10], '%Y-%m-%d')})
        self.env['common.rearrangement'].create(values)
        vals = {}
        if self._context.get('main_appointment'):
            if self.start_date and appointment \
                    .start_date != self.start_date:
                vals['start_date'] = self.start_date
            if self.end_date and appointment.end_date != self.end_date:
                vals['end_date'] = self.end_date
            if self.end_date and self.day_ids and \
                    appointment.week_days_ids.ids != self.day_ids.ids:
                vals['week_days_ids'] = [(6, 0, self.day_ids.ids)]
        if self.appointment_type_id and appointment \
                .appointment_type_id.id != self.appointment_type_id.id:
            vals['appointment_type_id'] = self.appointment_type_id.id
            vals['price_subtotal'] = self.appointment_type_id.price
        if self.group_appointment_booking_id:
            vals['appointment_date'] = self.appointment_date
            vals['day'] = self.appointment_date.strftime('%a').lower()
        if self.room_id and appointment.room_id.id != self.room_id.id:
            vals['room_id'] = self.room_id.id
        if self.physician_id and \
                appointment.physician_id.id != self.physician_id.id:
            vals['physician_id'] = self.physician_id.id
        if self.duration and appointment.duration != self.duration:
            vals['duration'] = self.duration
        if self.product_id and \
                appointment.product_id.id != self.product_id.id:
            vals['product_id'] = self.product_id.id
            vals['price_subtotal'] = self.product_id.lst_price
        if self.price_subtotal and \
                appointment.price_subtotal != self.price_subtotal:
            vals['price_subtotal'] = self.price_subtotal
        if self.start_time and appointment.start_time != self.start_time:
            vals['start_time'] = self.start_time
        if self.end_time and appointment.end_time != self.end_time:
            vals['end_time'] = self.end_time
        if vals:
            appointment.write(vals)
        return True
