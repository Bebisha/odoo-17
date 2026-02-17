# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api


class UpdateClinicalnotes(models.TransientModel):
    _name = 'wizard.update.clinical.note'
    _description = 'Update Appointment Clinical Notes'

    name = fields.Text(string="Clinical Note", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(UpdateClinicalnotes, self).default_get(fields_list)
        context = dict(self.env.context)
        if context.get('appointment_id') and \
                context.get('active_model') == 'appointment.appointment':
            appointment_id = self.env['appointment.appointment'].browse(
                context.get('appointment_id'))
            res.update({'name': appointment_id.clinical_notes or ''})
        return res


    def update_note(self):
        context = dict(self.env.context)
        if context.get('appointment_id') and \
                context.get('active_model') == 'appointment.appointment':
            appointment_id = self.env['appointment.appointment'].browse(
                context.get('appointment_id'))
            appointment_id.sudo().write({'clinical_notes': self.name})
        return True
