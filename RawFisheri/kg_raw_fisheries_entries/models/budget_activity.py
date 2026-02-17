# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BudgetActivity(models.Model):
    _name = 'budget.activity'
    _description = 'budget.activity'

    name = fields.Char(string='Name')
