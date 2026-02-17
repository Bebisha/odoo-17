# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
import warnings
# import odoo.addons.decimal_precision as dp
from odoo.addons.base.models.decimal_precision import DecimalPrecision
from datetime import datetime
from dateutil import relativedelta

from odoo.exceptions import UserError


class group_appointment(models.Model):
    _name = 'group.appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Group Appointment Creation'


    @api.depends('week_schedule_ids')
    def _compute_week_schedule(self):
        for group_appointment in self:
            if group_appointment.week_schedule_ids:
                group_appointment.week_schedule = True
            else:
                group_appointment.week_schedule = False

    @api.constrains('start_time', 'end_time')
    def _check_dates(self):
        """
            Start time must be prior to end time
        """
        for app in self:
            if app.start_time and app.end_time and \
                    app.start_time > app.end_time:
                raise UserError(_('Start time must be prior to end time'))

    name = fields.Char(string='Group Name', copy=False)
    date_line_ids = fields.One2many('group.dates.line', 'group_appointment_id',
                                    string='Date Line', copy=False)
    clinic_id = fields.Many2one('res.company', string='Clinic', copy=False,
                                default=lambda self:
                                self.env.user.company_id.id)
    group_size = fields.Integer(string='Group Size', copy=False, default=1)
    service_group_id = fields.Many2one('service.group',
                                       string='Service Group', copy=False)
    service_type_id = fields.Many2one('service.type',
                                      string='Service Type', copy=False)
    appointment_type_id = fields.Many2one('appointment.type',
                                          string='Appointment Type',
                                          copy=False)
    room_id = fields.Many2one('room.room', string="Room",
                              copy=False)
    physician_id = fields.Many2one('res.partner', string="Physician",
                                   domain=[('is_physician', '=', True)],
                                   copy=False)
    product_id = fields.Many2one('product.product', string='Price List',
                                 copy=False)
    price_subtotal = fields.Float(string='Amount',
                                  digits=(16,2),
                                  copy=False)
    week_schedule_ids = fields.One2many('physician.week.schedule',
                                        'group_appointment_id',
                                        string='Week Day Schedule', copy=False)
    whole_schedule_ids = fields.One2many('physician.whole.schedule',
                                         'group_appointment_id',
                                         string='Whole Schedule', copy=False)
    start_time = fields.Float(string='Start time',
                              copy=False)
    end_time = fields.Float(string="End Time",
                            copy=False)
    active = fields.Boolean(string='Active', copy=False, default=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('cancel', 'Cancelled')], string='State',
                             copy=False,
                             default='draft')
    week_schedule = fields.Boolean(string='Physician Week Schedule Generated',
                                   copy=False, store=True,
                                   compute='_compute_week_schedule')
    cancel_reason = fields.Text(string='Cancel Reason', copy=False)
    tdcc_group_appointment_id = fields.Integer(
        string='TDCC Group Appointment ID')


    def action_generate_whole_schedule(self):
        week_list = []
        holiday_obj = self.env['public.holidays']
        self.whole_schedule_ids.unlink()
        if not self.date_line_ids:
            raise UserError(_('Without start date and end date,'
                            'the group whole schedule list can be generated!'))
        if not self.week_schedule_ids:
            raise UserError(_('without Week schedule, can not process.'))
        for week_line in self.week_schedule_ids:
            week = {'day': week_line.day_list,
                    'start_time': week_line.start_time,
                    'end_time': week_line.end_time, }
            week_list.append(week)
        whole_schedule_obj = self.env['physician.whole.schedule']
        for date_line in self.date_line_ids:
            d1 = datetime.strptime(str(date_line.start_date), '%Y-%m-%d')
            d2 = datetime.strptime(str(date_line.end_date), '%Y-%m-%d')
            while d1 <= d2:
                domain = [('date', '=', str(d1.date())),
                          ('clinic_id', '=', self.clinic_id.id)]
                holiday_ids = holiday_obj.search(domain)
                if not holiday_ids:
                    for week in week_list:
                        if d1.strftime('%A').lower() == week['day']:
                            whole_schedule_vals = {'group_appointment_id':
                                                   self.id,
                                                   'date': str(d1.date()),
                                                   'start_time':
                                                   week['start_time'],
                                                   'end_time':
                                                   week['end_time'], }
                            whole_schedule_obj.create(whole_schedule_vals)
                d1 = d1 + relativedelta.relativedelta(days=1)
        if self.whole_schedule_ids:
            self.write({'state': 'confirm'})
        return True


    def action_plan_week_schedule(self):
        if self.week_schedule_ids:
            raise UserError(_('The Week Schedule has been already created.'))
        if not self.date_line_ids:
            raise UserError(_('Can not process without the '
                            'start date and end date !'))
        days_list = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday',
                     'friday', 'saturday']
        line_ids = []
        plan_week_schedule_obj = self.env['plan.week.schedule']
        for days in days_list:
            vals = (0, 0, {'allow': False if days == 'friday' else True,
                           'day_list': days,
                           'start_time': self.start_time or 0.00,
                           'end_time': self.end_time or 0.00})
            line_ids.append(vals)
        plan_week_schedule_id = plan_week_schedule_obj.create({'line_ids':
                                                               line_ids})
        view_id = self.env.ref('bista_tdcc_operations.plan_week_schedule_form')
        return {
            'name': _('Week Schedule'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'plan.week.schedule',
            'view_id': view_id and view_id.id or False,
            'type': 'ir.actions.act_window',
            'res_id': plan_week_schedule_id.id,
            'target': 'new',
        }

    @api.onchange('appointment_type_id')
    def change_appontment_type_id(self):
        if self.appointment_type_id:
            self.product_id = self.appointment_type_id.product_id.id
            if self.appointment_type_id.chargeable:
                self.price_subtotal = self.appointment_type_id.price or 0.00
            self.room_id = self.service_type_id.classroom_id and \
                self.service_type_id.classroom_id.id
            self.physician_id = self.service_type_id.physician_id and \
                self.service_type_id.physician_id.id

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        self.price_subtotal = self.product_id.lst_price or 0.00


    def action_cancel(self):
        self.ensure_one()
        if not self.cancel_reason:
            raise UserError(_('Could process! \n Without Cancellation Reason.'))
        self.write({'state': 'cancel'})


    def action_set_to_draft(self):
        self.ensure_one()
        self.week_schedule_ids.unlink()
        self.whole_schedule_ids.unlink()
        self.write({'state': 'draft'})


    def unlink(self):
        for group_appoint in self:
            if not group_appoint.state == 'draft':
                raise UserError(_("State in 'draft' can only delete."))
        super(group_appointment, self).unlink()


class group_dates_line(models.Model):
    _name = 'group.dates.line'
    _description = 'Group Appointment datas line'

    group_appointment_id = fields.Many2one('group.appointment',
                                           string='Group Appointment')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    _sql_constraints = [
        ('start_less_end', 'check(start_date <= end_date)',
         'End date should not lesser than start date.'),
    ]


class physician_week_schedule(models.Model):
    _name = 'physician.week.schedule'
    _description = 'Physician Week Schedule'

    group_appointment_id = fields.Many2one('group.appointment',
                                           string='Group Appointment')
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
        ('day_list_uniq', 'unique(day_list, group_appointment_id)',
         'Days per week must be unique.'),
    ]


class physician_whole_schedule(models.Model):
    _name = 'physician.whole.schedule'
    _description = 'Physician whole Schedule'

    group_appointment_id = fields.Many2one('group.appointment',
                                           string='Group Appointment')
    date = fields.Date(string='Date', required=True)
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
