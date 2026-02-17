# -*- coding: utf-8 -*-

from odoo import fields, models, _, api


class HRContract(models.Model):
    _inherit = 'hr.contract'

    housing_allowance = fields.Monetary(string="Housing Allowance")
    transportation_allowance = fields.Monetary(string="Transportation Allowance")
    other_allowances = fields.Monetary(string="Other Allowances")
    advance_payment = fields.Monetary(string="Advance payment")
    ot_rate = fields.Float(default='1.25', string='OT Rate',readonly=1)
