from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError

class KGAccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    normal_hours = fields.Float(string="Normal Hours")
    ot_hours = fields.Float(string="Overtime Hours")
    idle = fields.Float(string="Idle")
    anchorage = fields.Boolean(string="Anchorage", default=False)
    overseas = fields.Boolean(string="Overseas", default=False)
    progress = fields.Float(string="Task Progress", related="task_id.progress")
    time_in = fields.Datetime(string='Time In')
    time_out = fields.Datetime(string='Time Out')
    is_emp_entry_created = fields.Boolean(default=False, string="Is Emp Entry Created")
    vessel_id = fields.Many2one("vessel.code", string="Vessel", related="order_id.vessel_id", store=True)

    unit_amount = fields.Float(string='Quantity', compute='_compute_unit_amount', store=True)
    travel = fields.Boolean(string="Travel", default=False)

    @api.depends('idle', 'normal_hours', 'ot_hours')
    def _compute_unit_amount(self):
        for record in self:
            record.unit_amount = record.idle + record.normal_hours + record.ot_hours

    @api.onchange('anchorage')
    def change_anchorage(self):
        for rec in self:
            if rec.anchorage:
                rec.overseas = False

    @api.onchange('overseas')
    def change_overseas(self):
        for rec in self:
            if rec.overseas:
                rec.anchorage = False


    @api.model
    def create(self, vals):
        employee_id = vals.get('employee_id')
        date = vals.get('date')
        new_time = vals.get('time_in')

        if employee_id and date and new_time:
            lines = self.env['account.analytic.line'].search([
                ('employee_id', '=', employee_id),
                ('date', '=', date),
                ('time_in', '!=', False),
                ('unit_amount', '>', 0),
            ])

            for line in lines:
                start = line.time_in  # datetime
                if start <= new_time:
                    employee = self.env['hr.employee'].browse(employee_id)
                    raise UserError(_(
                        "Timesheet overlap detected.\n\n"
                        "The employee %s already has a timesheet entry that overlaps with the entered time."
                    ) % employee.name)

        return super().create(vals)

    # def write(self, vals):
    #     employee_id = vals.get('employee_id', self.employee_id.id)
    #     date = vals.get('date', self.date)
    #
    #     existing = self.env['account.analytic.line'].search([
    #         ('employee_id', '=', employee_id),
    #         ('date', '=', date),
    #         ('id', '!=', self.id)
    #     ])
    #     if existing:
    #         raise UserError("This employee already has a timesheet entry for this date.")
    #
    #     return super().write(vals)
