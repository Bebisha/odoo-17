# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
# import odoo.addons.decimal_precision as dp
from odoo.addons.base.models.decimal_precision import DecimalPrecision
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import  warnings



class GroupAppointmentBooking(models.Model):
    _name = 'group.appointment.booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Group Appointment Booking'

    name = fields.Char(string='Number', copy=False,default='/')
    group_appointment_id = fields.Many2one('group.appointment', string='Group',
                                           copy=False)
    client_ids = fields.Many2many('res.partner', string='Client',
                                  copy=False)
    clinic_id = fields.Many2one('res.company', string='Clinic', copy=False,

                                default=lambda self:
                                self.env.user.company_id.id)
    group_size = fields.Integer(string='Group Size', copy=False,
                            )
    allowed = fields.Integer(string='Allowed', copy=False)
    service_group_id = fields.Many2one('service.group',
                                       string='Service Group', copy=False,
                                    )
    service_type_id = fields.Many2one('service.type',
                                      string='Service Type', copy=False,
                                     )
    appointment_type_id = fields.Many2one('appointment.type',
                                          string='Appointment Type',
                                          copy=False,
                                         )
    room_id = fields.Many2one('room.room', string="Room",
                              copy=False,
                              )
    physician_id = fields.Many2one('res.partner', string="Physician",
                                   domain=[('is_physician', '=', True)],
                                   copy=False, )
    product_id = fields.Many2one('product.product', string='Price List',
                                 copy=False, )
    price_subtotal = fields.Float(string='Amount',
                                  digits=(16,2),
                                  copy=False,)
    appointment_ids = fields.One2many('appointment.appointment',
                                      'group_appointment_booking_id',
                                      string='Day Schedule', copy=False,
                                      domain=[('state', '!=', 'cancelled')])
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('cancel', 'Cancelled'),
                              ('invoiced', 'Invoiced')], string='State',
                             copy=False,
                             default='draft')
    date_generated = fields.Boolean(string='Date Generated', copy=False,
                                    store=True,
                                    compute='_compute_date_generated')
    week_days_ids = fields.Many2many('week.days', 'week_days_group_rel',
                                     'group_id', 'week_days_id',
                                     string="Comfort Days", copy=False,
                                     )
    user_id = fields.Many2one('res.users', string='User',
                              related='physician_id.user_id', store=True,
                              copy=False)
    common_cancellation_ids = fields.One2many('common.cancellation',
                                              'group_appointment_booking_id',
                                              string='Days Cancelled',
                                              copy=False)
    common_rearrangement_ids = fields.One2many('common.rearrangement',
                                               'group_appointment_booking_id',
                                               string='Days Rearrange',
                                               copy=False,
                                               )
    tdcc_group_appointment_booking_id = fields.Integer(
        string="TDCC Group Appointment Booking ID ")

    @api.constrains('client_ids', 'group_size')
    def _check_clients_length(self):
        if len(self.client_ids.ids) > self.group_size:
            raise ValidationError(_('You can select maximum %s clients')
                                  % self.group_size)


    def action_set_to_draft(self):
        self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'group.appointment.booking')
        return super(GroupAppointmentBooking, self).create(vals)


    def action_confirm(self):
        for group_appointment_booking in self:
            if not group_appointment_booking.physician_id:
                raise UserError(_('Could not process, select the physician!'))
            if not group_appointment_booking.product_id:
                raise UserError(_('Could not process, select the pricelist!'))
            for line in group_appointment_booking.appointment_ids.filtered(
                    lambda l: l.state != 'cancelled'):
                line.write({'state': 'confirmed'})
            group_appointment_booking.write({'state': 'confirm'})
        return True

    @api.onchange('group_appointment_id')
    def onchange_group_appointment_id(self):
        if not self.group_appointment_id:
            return
        days = []
        weekday_lst = []
        self.service_group_id = self.group_appointment_id. \
            service_group_id and self.group_appointment_id.\
            service_group_id.id or False
        self.service_type_id = self.group_appointment_id.service_type_id \
            and self.group_appointment_id.service_type_id.id or False
        self.appointment_type_id = self.group_appointment_id.\
            appointment_type_id and self.group_appointment_id.\
            appointment_type_id.id or False
        self.clinic_id = self.group_appointment_id.clinic_id and \
            self.group_appointment_id.clinic_id.id or False
        self.room_id = self.group_appointment_id.room_id and \
            self.group_appointment_id.room_id.id or False
        self.physician_id = self.group_appointment_id.physician_id and \
            self.group_appointment_id.physician_id.id or False
        self.group_size = self.group_appointment_id.group_size or 0
#            self.week_days_ids = [(6, 0, list_id)]
        for whole_days in self.group_appointment_id.whole_schedule_ids:
            date_day = datetime.strptime(str(whole_days.date), '%Y-%m-%d').\
                strftime('%a').lower()
            if date_day not in days:
                days.append(date_day)
        if days:
            weekday_ids = self.env['week.days'].search([('name', 'in', days)])
            for weekday_id in weekday_ids:
                weekday_lst.append(weekday_id.id)
        domain = {'week_days_ids': [('id', 'in', weekday_lst)]}
        return {'domain': domain}

    @api.onchange('appointment_type_id')
    def onchange_appontment_type_id(self):
        if self.appointment_type_id:
            self.product_id = self.appointment_type_id.product_id.id
            if self.appointment_type_id.chargeable and \
                    self.appointment_type_id.price:
                self.price_subtotal = self.appointment_type_id.price or 0.00

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        self.price_subtotal = self.product_id.lst_price or 0.00


    def action_comfort_days(self):
        context = dict(self._context)
        days_lst = [week_days.name for week_days in self.week_days_ids]
        line_ids = []
        view_id = self.env.ref('bista_tdcc_operations.'
                               'tdcc_client_date_comfortable_form')
        date_comfortable_obj = self.env['client.date.comfortable']
        for line in self.group_appointment_id.whole_schedule_ids:
            day = datetime.strptime(str(line.date), '%Y-%m-%d')\
                .strftime('%a').lower()
            if day in days_lst:
                values = (0, 0, {'allow': False,
                                 'date': line.date,
                                 'day': day,
                                 'start_time': line.start_time or 0.00,
                                 'end_time': line.end_time or 0.00,
                                 })
                line_ids.append(values)
        date_comfortable_id = date_comfortable_obj.create({'line_ids':
                                                           line_ids})
        context.update({'client_ids': self.client_ids.ids})
        return {
            'name': _('Comfortable Dates'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'client.date.comfortable',
            'view_id': view_id and view_id.id or False,
            'type': 'ir.actions.act_window',
            'res_id': date_comfortable_id.id,
            'target': 'new',
            'context': context
        }


    def action_send_mail(self):
        try:
            t = 'bista_tdcc_operations.group_appointment_booking_mail_template'
            template_id = self.env.ref(t)
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref(
                'mail.email_compose_message_wizard_form')
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'group.appointment.booking',
            'default_res_ids': self.ids,
            'default_partner_ids': [(6, 0, self.client_ids.ids)],
            'default_use_template': bool(template_id),
            'default_template_id': template_id and template_id.id,
            'default_composition_mode': 'comment',
            # 'custom_layout': "mail.mail_notification_borders",
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id.id, 'form')],
            'view_id': compose_form_id.id,
            'target': 'new',
            'context': ctx,
        }
