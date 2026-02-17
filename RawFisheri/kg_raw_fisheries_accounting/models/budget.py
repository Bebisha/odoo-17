# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'

    def action_mark_as_draft(self):
        for budget in self:
            budget.write({'state': 'draft'})
