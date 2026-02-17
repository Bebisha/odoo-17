# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    allow_commission = fields.Boolean(string="Entitled for commission")
    sales_limit = fields.Float(string="Sales Limit")
    cut_off_date = fields.Date(string="Cut off Date")
    commission_percentage = fields.Integer(string="Commission Percentage")
    commission_account_id = fields.Many2one('account.account',
                                            string="Commission Payable "
                                                   "Account",
                                            company_dependent=True)
    commission_expense_account_id = fields.Many2one('account.account',
                                                    string="Commission Expense"
                                                    "Account",
                                                    company_dependent=True)
