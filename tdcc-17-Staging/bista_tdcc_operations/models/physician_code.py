# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class PhysicianCode(models.Model):
    _name = 'physician.code'
    _description = 'Physician Code'

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active", default=True)
