# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    pdc_type = fields.Selection([('automatic', 'Automatic'),
                                 ('manual', 'Manual')], string='PDC Type',
                                default='manual')
    period_lock_date = fields.Date(
        string="Journals Entries Lock Date",
        tracking=True,
        help="Only users with the 'Adviser' role can edit accounts prior to and inclusive of this"
             " date. Use it for period locking inside an open fiscal year, for example.")