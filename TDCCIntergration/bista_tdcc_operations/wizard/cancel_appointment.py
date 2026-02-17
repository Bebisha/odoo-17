# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
import warnings

from odoo.exceptions import UserError


class AppointmentCancel(models.TransientModel):
    _name = 'appointment.cancel'
    _description = 'Appointment Cancel'

    cancel_reason_id = fields.Many2one('appointment.cancel.reason',
                                       string="Cancel Reason", required=True)
    with_end_date = fields.Boolean(string='With End Date', copy=False,
                                   default=False)
    from_date = fields.Date(string='From', copy=False)
    to_date = fields.Date(string='To', copy=False)
    client_id = fields.Many2one('res.partner', string='Client',
                                domain=[('is_student', '=', True)])

    def action_cancel_group_appointment(self, appointment_booking_id):
        if self.client_id:
            appointment_ids = appointment_booking_id.appointment_ids.filtered(
                lambda app: app.state in ('draft', 'confirmed', 'dna', 'invoiced') and app.client_id == self.client_id)
        else:
            appointment_ids = appointment_booking_id.appointment_ids.filtered(
                lambda app: app.state in ('draft', 'confirmed', 'dna', 'invoiced'))

        context = {'reason': self.cancel_reason_id}
        #         if not self.from_date and not self.to_date:
        #             appointment_booking_id.write({'state': 'cancel'})
        for each_appointment in appointment_ids:
            if self.from_date and self.to_date:
                if each_appointment.appointment_date >= \
                        self.from_date and \
                        each_appointment.appointment_date <= self.to_date:
                    related_inv = self.get_related_invoice(each_appointment)
                    if related_inv:
                        raise UserError(_('Please cancel invoice in order to '
                                        'cancel appointment.'))
                    each_appointment.with_context(context).action_cancel()
            elif (self.from_date and not self.to_date):
                if each_appointment.appointment_date >= self.from_date:
                    related_inv = self.get_related_invoice(each_appointment)
                    if related_inv:
                        raise UserError(_('Please cancel invoice in order to '
                                        'cancel appointment.'))
                    each_appointment.with_context(context).action_cancel()
            elif (not self.from_date and self.to_date):
                if each_appointment.appointment_date <= self.to_date:
                    related_inv = self.get_related_invoice(each_appointment)
                    if related_inv:
                        raise UserError(_('Please cancel invoice in order to '
                                        'cancel appointment.'))
                    each_appointment.with_context(context).action_cancel()
            else:
                related_inv = self.get_related_invoice(each_appointment)
                if related_inv:
                    raise UserError(_('Please cancel invoice in order to '
                                    'cancel appointment.'))
                each_appointment.with_context(context).action_cancel()

        if all(app.state == 'cancelled' for app in appointment_booking_id.appointment_ids):
            appointment_booking_id.write({'state': 'cancel'})
        return True

    def get_related_invoice(self, appointment_id):
        invoice_id = self.env['account.move'].search([
            ('appointment_id', '=', appointment_id.id),
            ('state', '!=', 'cancel')])
        return invoice_id

    def action_cancel_send(self):
        appo_obj = False
        # Group Appointment
        if self._context.get('active_model') == 'group.appointment.booking':
            appointment_booking_id = \
                self.env[self._context.get('active_model')].browse(
                    self._context.get('active_id'))
            self.action_cancel_group_appointment(appointment_booking_id)
            #             if not self.from_date and not self.to_date:
            #                 appointment_booking_id.write({'state': 'cancel'})
            return True

        # Normal Appointment
        if 'appointment_id' in self._context:
            appo_obj = self.env['appointment.appointment'].browse(
                int(self._context.get('appointment_id')))
            ctx = {'reason': self.cancel_reason_id,
                   'appointment': appo_obj.name,
                   'client': appo_obj.client_id.name,
                   'schedule_date': appo_obj.start_date,
                   }

            if appo_obj.end_date:
                appointment_line_ids = appo_obj.appointment_line_ids.filtered(
                    lambda l: l.state != 'cancelled')
                if self.from_date and self.to_date:
                    if appo_obj.start_date.date(
                    ) >= self.from_date and appo_obj.start_date.date(
                    ) <= self.to_date:
                        appo_obj.with_context(ctx).action_cancel()
                    for line in appointment_line_ids:
                        inv_state_active = False
                        related_inv = self.get_related_invoice(line)
                        if related_inv:
                            inv_state_active = True
                        if line.start_date.date() >= self.from_date and \
                                line. \
                                        start_date.date() <= self.to_date and \
                                line.start_date.date() > \
                                fields.Date.today():
                            if inv_state_active:
                                raise UserError(_("Please cancel invoice in order to cancel appointment."))
                            line.with_context(ctx).action_cancel()
                elif (self.from_date and not self.to_date):
                    if appo_obj.start_date.date(
                    ) >= self.from_date:
                        appo_obj.with_context(ctx).action_cancel()
                    for line in appointment_line_ids:
                        inv_state_active = False
                        related_inv = self.get_related_invoice(line)
                        if related_inv:
                            inv_state_active = True
                        if line.start_date.date() >= self.from_date and line. \
                                start_date.date() > \
                                fields.Date.today():
                            if related_inv:
                                raise UserError(_("Please cancel invoice in order to cancel appointment."))
                            line.with_context(ctx).action_cancel()
                elif (not self.from_date and self.to_date):
                    if appo_obj.start_date.date(
                    ) <= self.to_date:
                        appo_obj.with_context(ctx).action_cancel()
                    for line in appointment_line_ids:
                        inv_state_active = False
                        related_inv = self.get_related_invoice(line)
                        if related_inv:
                            inv_state_active = True

                        if line.start_date.date() <= self.to_date and line. \
                                start_date.date() > \
                                fields.Date.today():
                            if related_inv:
                                raise UserError(_("Please cancel invoice in order to cancel appointment."))
                            line.with_context(ctx).action_cancel()
                elif not self.from_date and not self.to_date:
                    appo_obj.with_context(ctx).action_cancel()
                    for line in appointment_line_ids:
                        inv_state_active = False
                        related_inv = self.get_related_invoice(line)
                        if related_inv:
                            inv_state_active = True
                            # raise Warning(_('Please cancel invoice in order '
                            #                 'to cancel appointment.'))
                            if line.invoice_count == 0 or not \
                                    inv_state_active:
                                line.with_context(ctx).action_cancel()
            else:
                appo_obj.with_context(ctx).action_cancel()

            """
            template = self.env.ref(
                'bista_tdcc_operations.appointment_cancellation_mail_template')
            ctx = {
                'reference': appo_obj.name,
                'send_to': ','.join(map(str, account_manager)),
                'client': appo_obj.client_id.name,
                'schedule_date': appo_obj.start_date,
            }
            self.env['mail.template'].browse(
                template.id).with_context(ctx).send_mail(
                self.id, force_send=True)
            """
