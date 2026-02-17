# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import warnings
from datetime import date, datetime


class CancelInvoiceRequest(models.TransientModel):
    _name = 'wizard.cancel.invoice.request'
    _description = 'Invoice Cancel Request'

    invoice_cancel_reason_id = fields.Many2one('appointment.cancel.reason',
                                               string="Invoice Cancel Reason")

    def cancel_invoice_request(self):
        context = dict(self.env.context)
        company_id = self.env.user.company_id
        if context.get('appointment_id') and \
                context.get('active_model') == 'appointment.appointment':
            appointment_id = self.env['appointment.appointment'].browse(
                context.get('appointment_id'))
            if appointment_id.invoice_id:
                if appointment_id.is_chargeable == 'chargeable' and \
                                appointment_id.state == 'dna':
                    raise UserError(_('Appointment is marked as chargeable you '
                                    'can not raise invoice cancel request!'))
                invoice = appointment_id.invoice_id
                if company_id.day_closing_date and invoice.invoice_date <= \
                        company_id.day_closing_date.date():
                    raise ValidationError(_('You can not raise invoice cancel '
                                            'request due to day has been '
                                            'closed.'))
                if invoice.state == 'cancel':
                    raise UserError(_('Invoice is already in cancelled \
                                    state,' 'You can not raise invoice \
                                    cancel request!'))
                invoice.sudo().write({
                    'invoice_cancel_reason_id' : self.invoice_cancel_reason_id.id,
                    'invoice_cancel_req': True,
                    'inv_cancel_req_date': datetime.now(),
                    'invoice_cancel_req_user_id': self.env.user.id,
                })
        return True
