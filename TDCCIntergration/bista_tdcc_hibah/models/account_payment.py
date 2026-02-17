# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = "Payments"

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        self.ensure_one()
        if self.env.context.get('from_sponsor_payment'):
            return {'domain': {'partner_id': [('is_sponsor', '=', True)]}}
        else:
            return {'domain': {'partner_id': [(self.partner_type, '=', True)]}}

    def _get_counterpart_move_line_vals(self, invoice=False):
        """
            - Set Journal label as Sponsor payment also set sponsor account id
        """
        res = super(AccountPayment, self)._get_counterpart_move_line_vals()
        if self.partner_id.is_sponsor and self.payment_type == 'inbound':
            if not self.partner_id.account_sponsor_id:
                raise ValidationError(
                    _('Please add Sponsor Account on Sponsor form'))
            res.update({'name': "Sponsor Payment",
                        'account_id':
                            self.partner_id.account_sponsor_id.id})
        return res
