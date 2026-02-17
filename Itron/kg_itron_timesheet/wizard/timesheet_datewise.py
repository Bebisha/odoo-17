from datetime import date
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TimesheetDatewiseWizard(models.TransientModel):
    _name = 'timesheet.datewise.wizard'
    _description = 'Datewise Timesheet Wizard'

    project_id = fields.Many2one('project.project',string="Project")
    company_id = fields.Many2one('res.company',string="Company", default=lambda self: self.env.company)
    employee_id = fields.Many2one('hr.employee', string="Employee", domain="[('company_id', '=', company_id)]")
    date_start = fields.Date(string="Start Date", required=True)
    date_end = fields.Date(string="End Date", required=True)


    @api.onchange('date_start','date_end')
    def onchange_dates(self):
        today = date.today()
        for rec in self:
            if rec.date_start and rec.date_end:
                if rec.date_start > rec.date_end:
                    raise ValidationError("The selected start date must be less than end date ")
                if rec.date_start > today or rec.date_end > today:
                    raise ValidationError("Future dates are not allowed.")


    def action_show_timesheets(self):
        print("action_show_timesheets")
        domain = [('date', '>=', self.date_start), ('date', '<=', self.date_end)]

        if self.employee_id:
            domain += [('employee_id', '=', self.employee_id.id)]
        if self.project_id:
            domain += [('project_id', '=', self.project_id.id)]
        if self.company_id:
            domain += [('company_id', '=', self.company_id.id)]

        return {
            'name': 'DateWise Timesheets',
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'tree,form',
            'domain': domain,
            'target': 'current',
        }