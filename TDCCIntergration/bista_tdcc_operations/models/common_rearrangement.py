# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields
# import odoo.addons.decimal_precision as dp
from odoo.addons.base.models.decimal_precision import DecimalPrecision


class CommonRearrangement(models.Model):
    _name = 'common.rearrangement'
    _description = 'Common rearrangement'
    _order = "id desc"

    name = fields.Char(related='appointment_id.name', string="Name")
    appointment_id = fields.Many2one('appointment.appointment',
                                     string='Appointment', copy=False,
                                     ondelete='cascade')
    appointment_type_id = fields.Many2one('appointment.type',
                                          string="Appointment Type")
    room_id = fields.Many2one('room.room', string="Room")
    duration = fields.Float(string="Duration")
    start_date = fields.Date(string='Start Date', copy=False)
    end_date = fields.Date(string='End Date', copy=False)
    rearrange_id = fields.Many2one('appointment.rearrange.reason',
                                   string='Reason for rearrange', copy=False)
    day_ids = fields.Many2many('week.days', 'week_appointment_rel',
                               'appointment_id', 'week_days_id', string='Days',
                               copy=False)
    appointment_week_day = fields.Selection([('sun', 'Sunday'),
                                             ('mon', 'Monday'),
                                             ('tue', 'Tuesday'),
                                             ('wed', 'Wednesday'),
                                             ('thu', 'Thursday'),
                                             ('fri', 'Friday'),
                                             ('sat', 'Saturday')],
                                            string='Day', copy=False)
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')
    write_by_id = fields.Many2one('res.users', string='By', copy=False)
    physician_id = fields.Many2one('res.partner', string='Physician',
                                   copy=False)
    client_id = fields.Many2one(related='appointment_id.client_id',
                                string="Client")
    product_id = fields.Many2one('product.product', string='Price List')
    price_subtotal = fields.Float(string='Amount',
                                  digits=(16,2))
    group_appointment_booking_id = fields.Many2one('group.appointment.booking')
