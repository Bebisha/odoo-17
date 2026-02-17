# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
import warnings

from odoo.exceptions import UserError


class PlanWeekSchedule(models.TransientModel):
    _name = 'plan.week.schedule'
    _description = 'Plan Week Schedule'

    line_ids = fields.One2many('plan.week.schedule.line',
                               'week_schedule_id', string='Schedule Line')


    def create_week_schedule(self):
        group_appointment_id = self._context.get('active_ids', [])[0]
        active_model = self._context.get('active_model')
        group_appointment_id = self.env[active_model].browse(
            group_appointment_id)
        allowed_lines = self.line_ids.filtered(lambda l: l.allow)
        week_schedule_obj = self.env['physician.week.schedule']
        if all([not line.allow for line in allowed_lines]):
            raise UserError(_('Atleast one day is required to process.'))
        for line in allowed_lines:
            week_schedule_obj.create({'day_list': line.day_list,
                                      'start_time': line.start_time or 0.00,
                                      'end_time': line.end_time or 0.00,
                                      'group_appointment_id':
                                      group_appointment_id.id,
                                      })
        return True


class PlanWeekScheduleLine(models.TransientModel):
    _name = 'plan.week.schedule.line'
    _description = 'Plan Week Schedule Line'

    week_schedule_id = fields.Many2one(
        'plan.week.schedule', string='Week Schedule')
    allow = fields.Boolean(string='Allow')
    day_list = fields.Selection([('sunday', 'Sunday'), ('monday', 'Monday'),
                                 ('tuesday', 'Tuesday'),
                                 ('wednesday', 'Wednesday'),
                                 ('thursday', 'Thursday'),
                                 ('friday', 'Friday'),
                                 ('saturday', 'Saturday')],
                                string='Schedule Days')
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')

    _sql_constraints = [
        ('day_list_uniq', 'unique(day_list,week_schedule_id)',
         'Days per week must be unique.'),
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
