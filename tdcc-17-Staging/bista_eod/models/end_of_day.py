# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api
from datetime import date

from datetime import date, datetime


class EndofDay(models.Model):
    _name = 'dashboard.eod'
    _description = "End of day process"

    def _get_eod_result(self):
        appointment_obj = self.env['appointment.appointment'].sudo()
        invoice_obj = self.env['account.move'].sudo()
        payment_obj = self.env['account.payment'].sudo()
        today_date = str(date.today())
        for eod in self:
            eod.dna_appointment_count = False
            eod.customer_inv_today_due_date_count = False
            eod.supplier_inv_today_due_date_count = False
            eod.unpaid_customer_payment_count = False
            eod.cancelled_appointment_count = False
            eod.customer_inv_past_due_date_count = False
            eod.supplier_inv_past_due_date_count = False
            eod.pdc_payment_count = False
            eod.cancelled_invoice_count = False
            eod.unattended_appointment_count = False
            eod.inv_cancel_req_count = False
            if eod.tile_type == 'appointment':
                dna_appointments = appointment_obj.search_count([
                    ('state', '=', 'dna'),
                    ('start_date', '>=', today_date + ' 00:00:00'),
                    ('start_date', '<=', today_date + ' 23:59:59')])
                cancelled_appointments = appointment_obj.search_count([
                    ('state', '=', 'cancelled'),
                    ('start_date', '>=', today_date + ' 00:00:00'),
                    ('start_date', '<=', today_date + ' 23:59:59')])
                unattended_appointments = appointment_obj.search_count([
                    ('state', 'in', ('new', 'confirmed')),
                    ('start_date', '<=', today_date + ' 23:59:59')
                ])
                eod.dna_appointment_count = dna_appointments
                eod.cancelled_appointment_count = cancelled_appointments
                eod.unattended_appointment_count = unattended_appointments
            if eod.tile_type == 'out_invoice':
                inv_today_due_date_ids = invoice_obj.search_count([
                    ('state', '=', 'open'),
                    ('invoice_date_due', '=', today_date),
                    ('move_type', '=', eod.tile_type)])
                inv_past_due_date_ids = invoice_obj.search_count([
                    ('state', '=', 'open'),
                    ('invoice_date_due', '<', today_date),
                    ('move_type', '=', eod.tile_type)])
                today_cancelled_inv_ids = invoice_obj.search_count([
                    ('state', '=', 'cancel'),
                    ('cancel_date', '=', today_date),
                    ('move_type', '=', eod.tile_type)])
                inv_cancel_req_ids = invoice_obj.search_count([
                    ('state', '!=', 'cancel'),
                    ('invoice_cancel_req', '=', True),
                    ('move_type', '=', eod.tile_type)])
                eod.customer_inv_today_due_date_count = inv_today_due_date_ids
                eod.customer_inv_past_due_date_count = inv_past_due_date_ids
                eod.cancelled_invoice_count = today_cancelled_inv_ids
                eod.inv_cancel_req_count = inv_cancel_req_ids
            if eod.tile_type == 'in_invoice':
                inv_today_due_date_ids = invoice_obj.search_count([
                    ('state', '=', 'open'),
                    ('invoice_date_due', '=', today_date),
                    ('move_type', '=', eod.tile_type)])
                inv_past_due_date_ids = invoice_obj.search_count([
                    ('state', '=', 'open'),
                    ('invoice_date_due', '<', today_date),
                    ('move_type', '=', eod.tile_type)])
                eod.supplier_inv_today_due_date_count = inv_today_due_date_ids
                eod.supplier_inv_past_due_date_count = inv_past_due_date_ids
            if eod.tile_type == 'customer_payment':
                pdc_payment_method_id = self.env.ref(
                    'bista_account_pdc.account_payment_method_pdc_in')
                payment_ids = payment_obj.search_count([('date', '=', today_date),
                    ('payment_type', '=', 'inbound'),
                    ('payment_method_line_id', '!=', pdc_payment_method_id.id),
                    ('partner_type', '=', 'customer')])
                pdc_payment_ids = payment_obj.search_count([('cheque_date', '=', today_date),
                    ('payment_type', '=', 'inbound'),
                    ('payment_method_line_id', '=', pdc_payment_method_id.id),
                    ('partner_type', '=', 'customer')])
                eod.unpaid_customer_payment_count = payment_ids
                eod.pdc_payment_count = pdc_payment_ids

    from datetime import date, datetime

    # def _get_eod_result(self):
    #     appointment_obj = self.env['appointment.appointment'].sudo()
    #     invoice_obj = self.env['account.move'].sudo()
    #     payment_obj = self.env['account.payment.register'].sudo()
    #     today_date = datetime.combine(date.today(), datetime.min.time())
    #
    #     for eod in self:
    #             if eod.tile_type == 'appointment':
    #                 dna_appointments = appointment_obj.search_count([
    #                     ('state', '=', 'dna'),
    #                     ('start_date', '>=', today_date),
    #                     ('start_date', '<=', today_date.replace(hour=23, minute=59, second=59))
    #                 ])
    #                 cancelled_appointments = appointment_obj.search_count([
    #                     ('state', '=', 'cancelled'),
    #                     ('start_date', '>=', today_date),
    #                     ('start_date', '<=', today_date.replace(hour=23, minute=59, second=59))
    #                 ])
    #                 unattended_appointments = appointment_obj.search_count([
    #                     ('state', 'in', ('new', 'confirmed')),
    #                     ('start_date', '<=', today_date.replace(hour=23, minute=59, second=59))
    #                 ])
    #                 eod.dna_appointment_count = dna_appointments
    #                 eod.cancelled_appointment_count = cancelled_appointments
    #                 eod.unattended_appointment_count = unattended_appointments
    #
    #             elif eod.tile_type in ('out_invoice', 'in_invoice'):
    #                 move_type = eod.tile_type
    #                 inv_today_due_date_ids = invoice_obj.search_count([
    #                     ('state', '=', 'open'),
    #                     ('invoice_date_due', '=', today_date.date()),
    #                     ('move_type', '=', move_type)
    #                 ])
    #                 inv_past_due_date_ids = invoice_obj.search_count([
    #                     ('state', '=', 'open'),
    #                     ('invoice_date_due', '<', today_date.date()),
    #                     ('move_type', '=', move_type)
    #                 ])
    #                 if move_type == 'out_invoice':
    #                     today_cancelled_inv_ids = invoice_obj.search_count([
    #                         ('state', '=', 'cancel'),
    #                         ('cancel_date', '=', today_date.date()),
    #                         ('move_type', '=', move_type)
    #                     ])
    #                     inv_cancel_req_ids = invoice_obj.search_count([
    #                         ('state', '!=', 'cancel'),
    #                         ('invoice_cancel_req', '=', True),
    #                         ('move_type', '=', move_type)
    #                     ])
    #                     eod.cancelled_invoice_count = today_cancelled_inv_ids
    #                     eod.inv_cancel_req_count = inv_cancel_req_ids
    #                 elif move_type == 'in_invoice':
    #                     eod.supplier_inv_today_due_date_count = inv_today_due_date_ids
    #                     eod.supplier_inv_past_due_date_count = inv_past_due_date_ids
    #                 else:
    #                     # Handle unexpected move_type
    #                     pass
    #
    #             elif eod.tile_type == 'customer_payment':
    #                 pdc_payment_method_id = self.env.ref(
    #                     'bista_account_pdc.account_payment_method_pdc_in')
    #                 payment_ids = payment_obj.search_count([
    #                     ('payment_date', '=', today_date.date()),
    #                     ('payment_type', '=', 'inbound'),
    #                     ('payment_method_line_id', '!=', pdc_payment_method_id.id),
    #                     ('partner_type', '=', 'customer')
    #                 ])
    #                 pdc_payment_ids = payment_obj.search_count([
    #                     ('cheque_date', '=', today_date.date()),
    #                     ('payment_type', '=', 'inbound'),
    #                     ('payment_method_line_id', '=', pdc_payment_method_id.id),
    #                     ('partner_type', '=', 'customer')
    #                 ])
    #                 eod.unpaid_customer_payment_count = payment_ids
    #                 eod.pdc_payment_count = pdc_payment_ids
    #
    #             else:
    #                 # Handle unexpected tile_type
    #                 pass

    name = fields.Char(string="Name")
    color = fields.Integer(string='Color Index')
    tile_type = fields.Selection([('appointment', 'Appointment'),
                                  ('in_invoice', 'Customer Invoice'),
                                  ('out_invoice', 'Vendor Bills'),
                                  ('customer_payment', 'Customer payment')])
    dna_appointment_count = fields.Integer(compute='_get_eod_result')
    cancelled_appointment_count = fields.Integer(compute='_get_eod_result')
    unattended_appointment_count = fields.Integer(compute='_get_eod_result')
    customer_inv_today_due_date_count = fields.Integer(
        compute='_get_eod_result')
    customer_inv_past_due_date_count = fields.Integer(
        compute='_get_eod_result')
    supplier_inv_today_due_date_count = fields.Integer(
        compute='_get_eod_result')
    supplier_inv_past_due_date_count = fields.Integer(
        compute='_get_eod_result')
    unpaid_customer_payment_count = fields.Integer(compute='_get_eod_result')
    pdc_payment_count = fields.Integer(compute='_get_eod_result')
    cancelled_invoice_count = fields.Integer(compute='_get_eod_result')
    inv_cancel_req_count = fields.Integer(compute='_get_eod_result')

    # @api.multi
    def action_open_appointment_view(self):
        action = False
        context = self.env.context
        today_date = str(date.today())
        action = self.env.ref(
            'bista_tdcc_operations.appointment_view_action').read()[0]
        if context.get('from_dna'):
            action['domain'] = [('state', '=', 'dna'),
                                ('start_date', '>=', today_date + ' 00:00:00'),
                                ('start_date', '<=', today_date + ' 23:59:59')]
        elif context.get('from_unattended'):
            action['domain'] = [('state', 'in', ('new', 'confirmed')),
                                ('start_date', '<=', today_date + ' 23:59:59')]

        elif context.get('from_cancel'):
            action['domain'] = [('state', '=', 'cancelled'),
                                ('start_date', '>=', today_date + ' 00:00:00'),
                                ('start_date', '<=', today_date + ' 23:59:59')]
        return action

    # @api.multi
    def action_open_invoice_view(self):
        action = {}
        context = self.env.context
        today_date = str(date.today())
        if self.tile_type == 'in_invoice':
            action = self.env.ref(
                'account.action_move_in_invoice_type').read()[0]
        elif self.tile_type == 'out_invoice':
            action = self.env.ref(
                'account.action_move_out_invoice_type').read()[0]
        else:
            action = self.env.ref(
                'account.action_account_payments').read()[0]

        if self.tile_type != 'customer_payment':
            domain = [('move_type', '=', self.tile_type)]
            if context.get('today_due'):
                domain += [('state', '=', 'open'),
                           ('invoice_date_due', '=', today_date)]
            elif context.get('from_cancel_invoice'):
                domain += [('state', '=', 'cancel'),
                           ('cancel_date', '=', today_date)]
            elif context.get('from_cancel_invoice_req'):
                domain += [('state', '!=', 'cancel'),
                           ('invoice_cancel_req', '=', True)]
            else:
                domain += [('state', '=', 'open'),
                           ('invoice_date_due', '<', today_date)]
            action['domain'] = domain
        elif context.get('from_pdc_payment'):
            action['domain'] = [('state', '!=', 'cancelled'),
                                ('cheque_date', '=', today_date),
                                ('payment_type', '=', 'inbound'),
                                ('payment_method_id', '=', self.env.ref(
                                    'bista_account_pdc.account_payment_method_pdc_in').id),
                                ('partner_type', '=', 'customer')]
            # ('state', '!=', 'cancelled'),
        else:
            action['domain'] = [('state', '!=', 'cancelled'),

                                ('payment_type', '=', 'inbound'),
                                ('partner_type', '=', 'customer')]
            # ('state', '!=', 'cancelled'),
        return action
