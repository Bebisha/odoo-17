# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################

from odoo import api, models, _, fields
from datetime import datetime, date
from odoo.exceptions import ValidationError


class DayClosing(models.TransientModel):
    _name = 'day.closing'
    _description = 'Day Closing'

    closing_date = fields.Datetime(string="Closing Date", required=True,
                                   default=datetime.now())
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    last_day_close_date = fields.Datetime(related='company_id.day_closing_date',
                                           string='Last Close Date')
    last_day_closing_user_id = fields.Many2one('res.users',
                                               related='company_id.day_closing_user_id',
                                               string='Last Day Closed By')


    def action_day_close(self):
        self.ensure_one()
        if self.closing_date.date() > date.today():
             raise ValidationError(_('You can not close the day for '
                                    'future date'))
        if self.closing_date.date() <= self.last_day_close_date.date():
             raise ValidationError(_('You can not close the day as day is \
                                      already closed for selected date.'))
        daily_note_count = self.env['daily.notes'].search_count([
            ('state', '=', 'draft')])
        if daily_note_count > 0:
            raise ValidationError(_('You can not close the day as there are '
                                    'undone daily notes.'))
        appointment_count = self.env['appointment.appointment'].search_count(
            [('state', 'in', ('new', 'confirmed')),
             ('start_date', '<=', self.closing_date.date())])
        if appointment_count > 0:
            raise ValidationError(_('You can not close the day as there are some '
                                    'appointments in Draft/Confirmed states.'))
        invoice_count = self.env['account.move'].search_count([
                    ('state', '!=', 'cancel'),
                    ('invoice_cancel_req', '=', True),
                    ('invoice_date', '<=', self.closing_date.date()),
                    ('move_type', '=', 'out_invoice')])
        if invoice_count > 0:
            raise ValidationError(_('You can not close the day as there are some '
                                    'invoices needs to be cancel.'))

        # Restrict Day closing if invoice is not generated for any appointments
        query = """
                SELECT  
                    ap.name from appointment_appointment ap
                WHERE 
                    ap.start_date :: date <= '%s'
                    """ % (self.closing_date.date()) + """ 
                    and ap.state in ('confirmed', 'arrive')
                    and (ap.is_chargeable IS NULL
                    OR ap.is_chargeable = 'chargeable')
                    and ap.id not in 
                    (SELECT
                        app.id 
                    FROM
                        appointment_appointment app
                        LEFT JOIN account_invoice ai
                        ON ai.id=app.invoice_id
                    WHERE app.invoice_id IS NOT NULL and app.start_date :: date <= '%s')
                        """ % (self.closing_date.date())
        self._cr.execute(query)
        res = self._cr.fetchall()
        if res:
            error_app = [r[0] for r in res]
            raise ValidationError(_('You can not close the day as invoice for \
                                         following Appointments are not generated \
                                        \n "%s" ')
                                  % (error_app))
#         Check Closing and Past Days DNA Appointment
        dna_appointment_ids = self.env['appointment.appointment'].search(
            [('state', '=', 'dna'),
             ('is_chargeable', '=', False),
             ('start_date', '<=', self.closing_date.date())])
        # Check appointments which are not marked as Arrived
        non_arrived_app_ids = self.env['appointment.appointment'].search(
            [('start_date', '<=', self.closing_date.date()),
             ('is_student_arrived', '=', False),
             ('state', 'in', ('confirmed', 'invoiced', 'done'))
             ])
        if non_arrived_app_ids:
            raise ValidationError(_('You can not close the day as following '
                                    'Appointments are not marked as Arrived or DNA \
                                    \n "%s" ')
                                  % (non_arrived_app_ids.mapped('name')))
        non_chargeable_app_ids = self.env['appointment.appointment'].search(
            [('state', '=', 'dna'),
             ('is_chargeable', '=', 'non_chargeable'),
             ('start_date', '<=', self.closing_date.date())])
        if dna_appointment_ids:
            raise ValidationError(_('You can not close the day as following '
                                    'Appointments are not marked as '
                                    'Chargeable/Non Chargeable \n "%s" ')
                                  % (dna_appointment_ids.mapped('name')))
        for non_app in non_chargeable_app_ids:
            if non_app.invoice_state != 'cancel':
                raise ValidationError(_('You can not close the day as Invoice '
                                        'of Appointment "%s" '
                                        'is not Cancelled.') % non_app.name)

#       #Check Only Closing Day DNA Appointment
#         closing_date = str(self.closing_date.date())
#         dna_appointment_ids = self.env['appointment.appointment'].search(
#             [('state', '=', 'dna'),
#              ('is_chargeable', '=', False),
#              ('start_date', '>=', closing_date + ' 00:00:00'),
#              ('start_date', '<=', closing_date + ' 23:59:59')])
#         if dna_appointment_ids:
#             raise ValidationError(_('You can not close the day as there are '
#                                     'some DNA Appointment which are not marked '
#                                     'as Chargeable/Non-Chargeable.'))
        company_id = self.env.user.company_id
        company_id.write({'day_closing_user_id': self.env.user.id,
                          'day_closing_date': self.closing_date})
        return {'type': 'ir.actions.act_window_close'}
