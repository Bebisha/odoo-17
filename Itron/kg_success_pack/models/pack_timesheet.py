# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import date

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
from ast import literal_eval


class PackTimesheet(models.Model):
    _name = "pack.timesheet"

    success_pack_line_id = fields.Many2one('kg.success.pack.line', 'Success Pack')
    pack_project_id = fields.Many2one('pack.projects', 'Pack Project', required=True)
    timesheet_ids = fields.Many2many('account.analytic.line', string='Timesheets')
    date = fields.Date(string='Date')
    hours_spent = fields.Float(string='Hours Spent')

    def action_print_pdf(self):
        return self.env.ref('kg_success_pack.action_report_pack_timesheet').report_action(self)

    def action_view_timesheet(self):
        timesheets = self.sudo().timesheet_ids
        action = {
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "name": _("Timesheets"),
            "context": {"create": False},
            "view_mode": "tree",
            "views": [(False, 'tree')],
            "target": "new",
            "domain": [('id', 'in', timesheets.ids)],
        }
        return action
