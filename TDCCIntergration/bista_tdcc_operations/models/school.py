# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class School(models.Model):
    _name = 'school.school'
    _description = 'School'

    name = fields.Char(string="Name")
    code = fields.Integer(string="Code")
    active = fields.Boolean(string="Active", default=True)
