# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api


class PublicHolidays(models.Model):
    _name = 'public.holidays'
    _description = 'Public Holidays'

    name = fields.Char(string="Name")
    date = fields.Date(string="Date")
    clinic_id = fields.Many2one("res.company",
                                string="Clinic",
                                copy=False,
                                default=lambda self:
                                self.env['res.company']._company_default_get(
                                    'public.holidays'))
    comment = fields.Text(string="Comment")
    active = fields.Boolean(string="Active", default=True)

    _sql_constraints = [
        ('unique_public_holiday', 'unique (date, clinic_id)',
         'Public Holiday with this date already exists!')
    ]

    @api.model
    def is_public_holiday(self, selected_date, clinic_id=False):
        domain = [('date', '=', selected_date)]
        if clinic_id:
            domain += [('clinic_id', '=', clinic_id)]
        holiday_ids = self.sudo().search(domain)
        if holiday_ids.ids:
            return True
        return False
