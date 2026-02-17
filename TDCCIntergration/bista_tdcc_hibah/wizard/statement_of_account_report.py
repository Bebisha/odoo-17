# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import models, fields, api


class StatementAccount(models.TransientModel):
    _name = "statement.account"
    _description = "Statement Of Account Report"

    partner_id = fields.Many2one('res.partner',
                                 domain=[('is_student', '=', True)],
                                 string="Client")
    date = fields.Date(string="Date as on")

    # @api.multi
    def print_report(self):
        form_data = {'partner_id': self.partner_id.id,
                     'date': self.date or False
                     }
        datas = {
            'ids': self._ids,
            'model': 'res.partner',
            'form_data': form_data,
        }
        return self.env.ref(
            'bista_tdcc_hibah.action_report_account_statement').report_action(
                self, data=datas)
