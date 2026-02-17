# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class UpdateAppointmentState(models.TransientModel):
    _name = 'update.appointment.state'
    _description = 'Update Appointment State'

    name = fields.Text(string="Clinical Note", required=False)
    state = fields.Selection([('dna', 'DNA'),
                              ('arrive', 'Arrived')],
                              default='arrive')

    @api.model
    def default_get(self, fields_list):
        res = super(UpdateAppointmentState, self).default_get(fields_list)
        context = dict(self.env.context)
        if context.get('appointment_id') and \
                context.get('active_model') == 'appointment.appointment':
            appointment_id = self.env['appointment.appointment'].browse(
                context.get('appointment_id'))
        return res


    def update_state(self):
        context = dict(self.env.context)
        day_close_date = self.env.user.company_id.day_closing_date
        active_id = context.get('active_id')
        if active_id and \
                context.get('active_model') == 'appointment.appointment':
            appointment_id = self.env['appointment.appointment'].browse(
                active_id)
            app_start_date = appointment_id.start_date.date()
            if app_start_date <= day_close_date.date():
                raise ValidationError(_('Day is closed for appointment \
                                    date "%s"') %app_start_date)
            elif app_start_date > day_close_date.date():
                if self.state == 'arrive':
                    is_student_arrived = True
                else:
                    is_student_arrived = False
                appointment_id.write({
                    'state': self.state,
                    'is_student_arrived': is_student_arrived})
        return True
