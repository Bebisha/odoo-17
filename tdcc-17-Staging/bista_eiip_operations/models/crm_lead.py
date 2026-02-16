# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    group_id = fields.Many2one('eiip.group', string='Group')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
