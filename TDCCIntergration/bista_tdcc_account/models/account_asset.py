# -*- encoding: utf-8 -*-
##############################################################################
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset'

    prepayment_expense = fields.Boolean(string='Prepayment Expense')


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'

    prepayment_expense = fields.Boolean(string='Prepayment Expense')
