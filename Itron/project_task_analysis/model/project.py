from odoo import models, fields, api, _
from datetime import date, timedelta
import logging

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProjectTasks(models.Model):
    _inherit = 'project.task'

    date_start = fields.Date("Start Date", traking=True)
    hours_spent_avg = fields.Boolean(string="Take Average")
    user_ids = fields.Many2many('res.users', string="Assigned to", default=lambda self: self.env.user, )

    @api.depends('user_ids.company_id')
    def _compute_company_id(self):
        for task in self:
            if not task.user_ids:
                continue

            company_ids = task.user_ids.mapped('company_id')
            if len(company_ids) == 1:
                task.company_id = company_ids[0]
            else:
                raise ValidationError("Please select users from the same company.")

    @api.depends('hours_spent_avg', 'timesheet_ids.unit_amount')
    def _compute_effective_hours(self):
        for task in self:
            if task.hours_spent_avg:
                print('True------------------')
                total_hour_spent = sum(task.timesheet_ids.mapped('unit_amount'))
                if task.allocated_hours != 0 and total_hour_spent > task.allocated_hours:
                    task.effective_hours = total_hour_spent / len(task.user_ids)
            else:
                print('False---------------------')
                return super(ProjectTasks, task)._compute_effective_hours()
            # if not any(self._ids):
            #     for task in self:
            #         task.effective_hours = sum(task.timesheet_ids.mapped('unit_amount'))
            #     return
            # timesheet_read_group = self.env['account.analytic.line']._read_group([('task_id', 'in', self.ids)], ['task_id'],
            #                                                                      ['unit_amount:sum'])
            # timesheets_per_task = {task.id: amount for task, amount in timesheet_read_group}
            # for task in self:
            #     task.effective_hours = timesheets_per_task.get(task.id, 0.0)

    @api.constrains('date_start', 'date_deadline')
    def update_date_start(self):
        for task in self:
            if task.date_start and task.date_deadline:
                if task.date_start > task.date_deadline:
                    raise ValidationError(_('Start Date must be less than End Date'))
                # message_body = f'Start Date Has Been Changed to <b>{task.date_start.strftime("%m-%d-%Y")} </b>'
                # task.message_post(body=message_body)

    @api.constrains('date_start')
    def update_date_start_log(self):
        for task in self:
            if task.date_start:
                message_body = f'Start Date Has Been Changed to {task.date_start.strftime("%m-%d-%Y")} '
                task.message_post(body=message_body)

    @api.constrains('date_deadline')
    def update_date_end_log(self):
        for task in self:
            if task.date_deadline:
                message_body = f'Deadline Has Been Changed to {task.date_deadline.strftime("%m-%d-%Y")} '
                task.message_post(body=message_body)

    criticality = fields.Selection([
        ('critical', 'Critical'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string="Criticality")
    task_type = fields.Selection(
        string='Task Type',
        selection=[
            ('development', 'Development'),
            ('bug', 'Bug'),
            ('cr', 'Change Request'),
            ('investigation', 'Investigation'),
            ('development', 'Development'),
            ('ra', 'Requirement Analysis'),
            ('enhance', 'Enhancement'), ('testing', 'Testing')],
        default='development', )

    @api.model
    def create(self, vals):
        if vals.get('allocated_hours', 0.0) <= 0.0:
            raise ValidationError("Please enter Allocated Time.")
        return super(ProjectTasks, self).create(vals)

    def write(self, vals):
        if 'allocated_hours' in vals:
            for task in self:
                if task.allocated_hours and vals['allocated_hours'] != task.allocated_hours:
                    raise ValidationError("You cannot modify Allocated Time after creation.")
        return super().write(vals)
