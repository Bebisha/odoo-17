# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class AppointmentRearrangeReason(models.Model):
    _name = 'appointment.rearrange.reason'
    _description = 'Appointment Rearrange Reason'

    name = fields.Char(string="Name")
    code = fields.Integer(string="Code")
    active = fields.Boolean(string="Active", default=True)
