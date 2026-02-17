# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class ServiceType(models.Model):
    _name = 'service.type'
    _description = 'Service Type'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    clinic_id = fields.Many2one("res.company",
                                string="Clinic",
                                copy=False,
                                default=lambda self: self.env[
                                    'res.company']._company_default_get())
    classroom_id = fields.Many2one("room.room",
                                   string="Room")
    physician_id = fields.Many2one("res.partner",
                                   string="Physician")
    service_group_id = fields.Many2one("service.group",
                                       string="Service Group")
    active = fields.Boolean(string="Active", default=True)
    appointment_type_ids = fields.One2many("appointment.type",
                                           inverse_name="service_type_id",
                                           string="Appointment Type")
    summary = fields.Text
