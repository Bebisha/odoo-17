# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    commission_journal_id = fields.Many2one('account.journal',
                                            string="Commission Journal")


    @api.model
    def get_values(self):
        ICP = self.env['ir.config_parameter'].sudo()
        res = super(ResConfigSettings, self).get_values()
        res.update(commission_journal_id=int(ICP.get_param(
            'bista_tdcc_commission.commission_journal_id', default=False)))
        return res

    # @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('bista_tdcc_commission.commission_journal_id',
                         self.commission_journal_id.id or False)
        return res
