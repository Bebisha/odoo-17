from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError

class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.constrains('allocated_hours')
    def _check_spent_hrs(self):
        for record in self:
            amc_records = self.env['project.contract.request.amc'].search([
                ('project_id', '=', record.project_id.id),
                ('date_start', '<=', record.date_start),
                ('date_end', '>=', record.date_deadline),
            ])
            total_spent_hrs = sum(amc_records.mapped('spent_hrs'))-record.allocated_hours
            total_planned_hrs = sum(amc_records.mapped('planned_hrs'))

            if total_planned_hrs != 0 and total_spent_hrs > total_planned_hrs:
                raise ValidationError(
                    "Spent hours cannot exceed planned hours for the AMC Project: %s. Planned: %s, Spent: %s" % (record.project_id.name,
                        total_planned_hrs, total_spent_hrs)
                )