# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com)
# Author : Nicolas Bessi (Camptocamp)

from odoo import fields,models,api

class res_company(models.Model):
    """Override company to add Header object link a company can have many header and logos"""

    _inherit = "res.company"

    kg_bank_details = fields.Text(string="Bank Details")

