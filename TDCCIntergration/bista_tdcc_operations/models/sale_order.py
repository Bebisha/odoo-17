# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api


class SaleorderLine(models.Model):
    _inherit = 'sale.order.line'

    service_type_id = fields.Many2one('service.type', string="Service Type",
                                      copy=False)
    appointment_date = fields.Datetime(string="Appointment Date")

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleorderLine, self)._prepare_invoice_line(**optional_values)
        res.update({'service_type_id': self.service_type_id.id})
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_view_appointment(self):
        appointments = self.env['appointment.appointment'].search(
            [('sale_id', '=', self.id)])
        action = self.env.ref(
            'bista_tdcc_operations.appointment_view_action').read()[0]
        if len(appointments) > 1:
            action['domain'] = [('id', 'in', appointments.ids)]
        elif len(appointments) == 1:
            action['views'] = [
                (self.env.ref(
                    'bista_tdcc_operations.appointment_appointment_form').id,
                 'form')]
            action['res_id'] = appointments.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.depends()
    def count_appointments(self):
        self.ensure_one()
        appointments = self.env['appointment.appointment'].search_count(
            [('sale_id', '=', self.id)])
        self.appointment_count = appointments

    #     service_group_id = fields.Many2one('service.group',
    #                                        string="Service Group",
    #                                        copy=False)
    #     service_type_id = fields.Many2one('service.type', string="Service Type",
    #                                       copy=False)
    program_type = fields.Selection([('eip', 'EIP'), ('eiip', 'EIIP'),
                                     ('360', '360'), ],
                                    string="Program Type",
                                    copy=False, default='eip')
    # term_id = fields.Many2one('academic.term',string="Term")
    class_id = fields.Many2one('school.classroom', string="Class")
    payment_info = fields.Char(string='Payment Information')
    finance_administrator = fields.Char(string="Finance Administrator")
    appointment_count = fields.Integer(compute='count_appointments',
                                       string="Appointments")

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({'class_id': self.class_id.id})
        return res

    @api.onchange('team_id')
    def onchange_team(self):
        if not self.team_id:
            return
        self.program_type = self.team_id.program_type

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for rec in self:
            if rec.partner_id.payment_info:
                rec.payment_info = rec.partner_id.payment_info
