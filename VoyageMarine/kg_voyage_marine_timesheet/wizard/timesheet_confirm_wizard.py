# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import UserError


class TimesheetConfirmWizard(models.TransientModel):
    _name = 'timesheet.confirm.wizard'
    _description = 'Confirm Duplicate Timesheet Creation'


    project_id = fields.Many2one(
        'project.project',
        string='Project',
    )

    line_id = fields.Many2one(
        'time.entry.line',
        string='Entry Line',
    )
    duplicate_line_ids = fields.Many2many(
        'time.entry.line',
        string='Duplicate Lines'
    )

    def action_confirm(self):
        AnalyticLine = self.env['account.analytic.line']

        for line in self.duplicate_line_ids:
            AnalyticLine.create({
                'name': 'Timesheet Entry',
                'project_id': self.project_id.id,
                'task_id': line.subtask_id.id,
                'user_id': line.assignee_id.id,
                'employee_id': (
                    line.assignee_id.employee_id.id
                    if line.assignee_id.employee_id else False
                ),
                'date': line.time_in.date(),
                'time_in': line.time_in,
                'overseas': line.overseas,
                'anchorage': line.anchorage,
                'unit_amount': line.total_hours,
            })

        return {'type': 'ir.actions.act_window_close'}
