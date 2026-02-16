# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import fields, models


class ResBank(models.Model):
    _inherit = 'res.bank'

    bank_branch = fields.Char('Bank Branch')
