# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class ServiceGroup(models.Model):
    _name = 'service.group'
    _description = 'Service Group'

    name = fields.Char(string="Name")
    active = fields.Boolean(string="Active", default=True)
    service_type_ids = fields.One2many("service.type",
                                       inverse_name="service_group_id",
                                       string="Service Types")
