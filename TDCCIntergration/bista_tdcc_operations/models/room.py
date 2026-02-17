# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class Room(models.Model):
    _name = 'room.room'
    _description = 'Room'

    name = fields.Char(string="Name")
    clinic_id = fields.Many2one('res.company',
                                string='Clinic',
                                copy=False,
                                default=lambda self: self.env[
                                    'res.company']._company_default_get())
    active = fields.Boolean(string="Active", default=True)
