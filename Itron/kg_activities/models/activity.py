from odoo import fields, models, api, exceptions, _
from datetime import datetime, date


class CustomActivityModel(models.Model):
    _name = "custom.activity"
    _description = "Custom Activity Model"
    _inherit = ["mail.activity.mixin", "mail.thread"]

    name = fields.Char()


class MailActivity(models.Model):
    _inherit = "mail.activity"

    planned_hrs = fields.Float(string='Planned hours')
    hours_spent = fields.Float(string='Hours Spent', compute='_compute_hours_spend')
    start_date = fields.Date(string='Start Date', default=date.today())
    helpdesk_id = fields.Many2one('helpdesk.ticket', string='Helpdesk', readonly=True)
    stage = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),

    ], default='draft', string='Status', copy=False)

    def _compute_hours_spend(self):
        """ compute hours spent based on timesheet """
        for record in self:
            timesheets = self.env['account.analytic.line'].search([
                ('activity_id', '=', record.id),
                ('date', '>=', record.start_date),
                ('date', '<=', record.date_deadline),
            ])
            total_hours = sum(timesheet.unit_amount for timesheet in timesheets)
            record.write({'hours_spent': total_hours or 0})
