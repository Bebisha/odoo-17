# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class WeekDays(models.Model):
    _name = "week.days"
    _description = 'Week Days'

    name = fields.Selection([('sun', 'Sunday'), ('mon', 'Monday'),
                             ('tue', 'Tuesday'),
                             ('wed', 'Wednesday'), ('thu', 'Thursday'),
                             ('fri', 'Friday'), ('sat', 'Saturday')],
                            string='Day')
