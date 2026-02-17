# -*- coding: utf-8 -*-

from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'account.analytic.account'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    parent_id = fields.Many2one('account.analytic.account', string='Parent')
    parent_path = fields.Char(index=True, unaccent=False)
    show_in_mc = fields.Boolean(string='Show in Report')
    management_cost = fields.Boolean(string='Management Cost')
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name', recursive=True,
        store=True)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for analytic in self:
            if analytic.parent_id:
                analytic.complete_name = f"{analytic.parent_id.complete_name} / {analytic.name}"
            else:
                analytic.complete_name = analytic.name

    @api.model
    def name_create(self, name):
        analytic = self.create({'name': name})
        return analytic.id, analytic.display_name

    @api.depends_context('hierarchical_naming')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.complete_name or record.name


