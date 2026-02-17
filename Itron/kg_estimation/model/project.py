from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Project(models.Model):
  _inherit = 'project.task'

  def _compute_estimation(self):
        rec = self.env['sales.estimation'].search([('project_id', '=', self.project_id.id)])
        self.estimation_id = rec

  estimation_line_id = fields.Many2one('sales.estimation.lines', string=" Estimation Line")
  estimation_id = fields.Many2one('sales.estimation',compute=_compute_estimation)
  priority = fields.Selection([
      ('0', 'Show Stopper'),
      ('1', 'High'),('2', 'Medium'),('3', 'Low'),], default='2', index=True, string="Priority", tracking=True)
  date_deadline = fields.Date(string='Deadline', index=True, copy=False, tracking=True, required=False, task_dependency_tracking=True, default=fields.Date.context_today)

  date_from = fields.Date('Date From', index=True, default=fields.Date.context_today)
  date_to = fields.Date('Date To',  index=True, default=fields.Date.context_today)


class AccountAnalyticLine(models.Model):
  _inherit = 'account.analytic.line'

  estimation_id = fields.Many2one('sales.estimation',string=" Estimation")
  estimation_line_id = fields.Many2one('sales.estimation.lines', string=" Estimation Line")