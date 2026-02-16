# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SponsorPaymentDetails(models.TransientModel):
    _name = "sponsor.payment.details"
    _description = "Sponsor Payments Details"

    partner_id = fields.Many2one('res.partner', string="Sponsor")
    from_date = fields.Date(string="Start Date")
    to_date = fields.Date(string="End Date")

    # @api.multi
    def print_report(self):
        self.ensure_one()
        if (self.from_date and self.to_date) and \
                self.to_date < self.from_date:
            raise UserError(_(
                'End date should be greater than start date.'))

        form_data = {'partner_id': self.partner_id.id,
                     'from_date': self.from_date or False,
                     'to_date': self.to_date or False}
        datas = {
            'ids': self._ids,
            'model': 'res.partner',
            'form_data': form_data,
        }
        return self.env.ref(
            'bista_tdcc_hibah.action_report_sponsor_payment').report_action(
                self, data=datas)
