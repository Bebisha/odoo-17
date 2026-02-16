# -*- coding: utf-8 -*-

from odoo import models, fields, api


class KgBranch(models.Model):
    _name = 'kg_branch'
    _description = 'kg_branch'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False,
                                 default=lambda self: self.env.company)
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

