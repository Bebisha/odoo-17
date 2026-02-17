# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api


class Partner(models.Model):
    _inherit = 'res.partner'

    account_sponsor_id = fields.Many2one('account.account',
                                         string="Account Sponsor",
                                         help="This account will be current "
                                              "liability type of account used "
                                              "to collect fund from "
                                              "this sponsor")

    @api.onchange('is_sponsor')
    def _change_is_sponsor(self):
        """
            - If is_sponsor set False then sponsor account set False
        """
        for partner in self:
            if not partner.is_sponsor:
                partner.account_sponsor_id = False
