# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
import warnings


class daily_appointment_wizard(models.TransientModel):
    _name = "daily.appointment.wizard"
    _description = 'Daily Appointment Wizard'

    client_id = fields.Many2one('res.partner',
                                string="Clients",
                                domain=[('is_student', '=',
                                         True)])
    clinic_id = fields.Many2one('res.company',
                                string="Clinic",
                                copy=False,
                                default=lambda self: self.env[
                                    'res.company']._company_default_get())
    physician_id = fields.Many2one(
        'res.partner', domain=[('is_physician', '=', True)], default=lambda self: self._get_default_physician())

    @api.model
    def _get_default_physician(self):
        return self.env.user.partner_id if self.env.user.partner_id.is_physician else False

    room_id = fields.Many2one('room.room', string="Room")
    start_date = fields.Date(
        string='Start Date',
        default=fields.Date.context_today)
    end_date = fields.Date(
        string='End Date',
        default=fields.Date.context_today)
    print_pdf = fields.Boolean(string='Print', default=False)
    code_id = fields.Many2one('physician.code', string='Code')
    app_with_bal = fields.Boolean(string="Show negative balance", default=True)
    duration = fields.Float(string="Duration")

    @api.onchange('start_date')
    def onchange_date(self):
        if self.start_date:
            self.end_date = self.start_date

    # def open_appointments(self):
    #     user_id = self.env.user
    #     practitionar_group = 'bista_tdcc_operations.group_tdcc_practitioner'
    #
    #     if not self.print_pdf:
    #         domain = [('start_date', '>=', str(self.start_date)),
    #                   ('start_date', '<=', str(self.end_date)),
    #                   ('state', '!=', 'cancelled')]
    #         if self.code_id:
    #             physician_id = self.env['res.partner'].search(
    #                 [('physician_code_id', '=', self.code_id.id)])
    #             domain += [('physician_id', 'in', physician_id.ids)]
    #         if self.physician_id and not self.code_id:
    #             domain += [('physician_id', '=', self.physician_id.id)]
    #         if self.clinic_id:
    #             domain += [('clinic_id', '=', self.clinic_id.id)]
    #         if self.room_id:
    #             domain += [('room_id', '=', self.room_id.id)]
    #         if not self.app_with_bal:
    #             domain += [('credit', '>', 0.00)]
    #
    #         action = self.env.ref('bista_tdcc_operations.daily_appointment_view_action').read()[0]
    #         action['domain'] = domain
    #         return action
    #     else:
    #         [data] = self.read()
    #         form_data = {
    #             'physician_id': self.physician_id.id,
    #             'start_date': self.start_date,
    #             'end_date': self.end_date,
    #             'code_id': self.code_id.id,
    #             'clinic_id': self.clinic_id.id,
    #             'room_id': self.room_id.id
    #         }
    #         datas = {
    #             'ids': self._ids,
    #             'model': 'appointment.appointment',  # Adjust this model name as per your actual model
    #             'form': data,
    #             'form_data': form_data
    #         }
    #         # Assuming 'bista_tdcc_operations.daily_appointment_report' is the XML ID of your report action
    #         report_action = self.env['ir.actions.report'].search(
    #             [('report_name', '=', 'bista_tdcc_operations.daily_appointment_report')], limit=1)
    #         if report_action:
    #             return report_action.report_action(self, data=datas)
    #         else:
    #             # Handle the case where report action is not found
    #             return {
    #                 'type': 'ir.actions.act_window',
    #                 'view_mode': 'form',
    #                 'res_model': 'daily.appointment.wizard',
    #                 'target': 'current',
    #                 'context': self.env.context,
    #             }
    def open_appointments(self):
        user_id = self.env.user
        practitionar_group = 'bista_tdcc_operations.group_tdcc_practitioner'
        domain = [('start_date', '>=', self.start_date),
                  ('start_date', '<=', self.end_date),
                  ('state', '!=', 'cancelled')]
        if self.code_id:
            physician_id = self.env['res.partner'].search(
                [('physician_code_id', '=', self.code_id.id)])
            # if physician_id:
            domain += [('physician_id', 'in', physician_id.ids)]
        if self.physician_id and not self.code_id:
            domain += [('physician_id', '=', self.physician_id.id)]
        if self.clinic_id:
            domain += [('clinic_id', '=', self.clinic_id.id)]
        if self.room_id:
            domain += [('room_id', '=', self.room_id.id)]

        if not self.print_pdf:
            if not self.app_with_bal:
                domain += [('credit', '>', 0.00)]
            action = self.env.ref(
                'bista_tdcc_operations.daily_appointment_view_action').read()[0]
            action['domain'] = domain
            return action
        else:
            data_list=[]
            appointment = self.env['appointment.appointment'].search(domain)
            for rec in appointment:

                form_data = {
                    'physician_id': rec.physician_id.name,
                    'date': rec.start_date,
                    'duration': rec.duration,
                    'clinic_id': rec.clinic_id.name,
                    'room_id': rec.room_id.name,
                    'name': rec.name,
                    'client_id': rec.client_id.name,
                    'time': rec.start_date.time()
                    # 'code_id': rec.code_id.name,

                }
                data_list.append(form_data)
                print(form_data,'sssssssssssssss')
            [data] = self.read()
            datas = {
                'ids': self._ids,
                'model': 'appointment.appointment',
                'form': data,
                'form_data': data_list
            }
            print(datas,'datas')
            print(self.env.ref('bista_tdcc_operations.action_report_leave_settlement').report_action(self, data=datas),
                  'qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq')
            return self.env.ref('bista_tdcc_operations.action_report_leave_settlement').report_action(self, data=datas)
