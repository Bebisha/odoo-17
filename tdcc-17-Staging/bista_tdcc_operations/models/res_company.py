# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    dha_license_no = fields.Char(string="DHA License No")
    cda_license_no = fields.Char(string="CDA License no")
    day_closing_user_id = fields.Many2one('res.users',
                                          string="Day Close by")
    day_closing_date = fields.Datetime(string='Day Closing on')
