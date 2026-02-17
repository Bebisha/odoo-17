# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class CommonCancellation(models.Model):
    _name = 'common.cancellation'
    _description = 'Common Cancellation'
    _order = "id desc"

    name = fields.Char(related='appointment_id.name', string="Name")
    appointment_id = fields.Many2one(
        'appointment.appointment',
        string='Appointment',
        copy=False, ondelete='cascade')
    client_id = fields.Many2one(related='appointment_id.client_id',
                                string="Client")
    date = fields.Date(string='Date', copy=False)
    cancel_id = fields.Many2one(
        'appointment.cancel.reason',
        string='Reason for Cancel',
        copy=False)
    day = fields.Selection([('sun',
                             'Sunday'),
                            ('mon',
                             'Monday'),
                            ('tue',
                             'Tuesday'),
                            ('wed',
                             'Wednesday'),
                            ('thu',
                             'Thursday'),
                            ('fri',
                             'Friday'),
                            ('sat',
                             'Saturday')],
                           string='Day',
                           copy=False)
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')
    write_by_id = fields.Many2one('res.users', string='By', copy=False)
    physician_id = fields.Many2one(
        'res.partner', string='Physician', copy=False)
    group_appointment_booking_id = fields.Many2one('group.appointment.booking')
