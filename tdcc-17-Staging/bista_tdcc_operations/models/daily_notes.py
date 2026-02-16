# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api
from datetime import date


class DailyNotes(models.Model):
    _name = 'daily.notes'
    _description = 'Physician Daily Notes'

    name = fields.Char(string="Title", required=True)
    description = fields.Text(string="Description")
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], default='draft')
    user_id = fields.Many2one('res.users', string="Practitioner",
                              default=lambda self: self.env.user.id)

    @api.model
    def get_dailynotes(self):
        today_date = str(date.today())
        dailynotes_count = self.search_count([('state', '=', 'draft')])
        dna_appointment_count = self.env['appointment.appointment'].search_count([
                    ('state', '=', 'dna'),
                    ('start_date', '>=', today_date + ' 00:00:00'),
                    ('start_date', '<=', today_date + ' 23:59:59')])
        inv_cancel_request_count = self.env['account.move'].search_count([
            ('move_type', '=', 'out_invoice'), ('invoice_cancel_req', '=', True)])
        return {'dailynotes_count':dailynotes_count ,
                'dna_appointment_count':dna_appointment_count,
                'inv_cancel_request_count': inv_cancel_request_count}


    def action_done(self):
        for rec in self:
            rec.state = 'done'
        #     rec.write({'state': 'approved'})
        # return self.write({'state': 'done'})
