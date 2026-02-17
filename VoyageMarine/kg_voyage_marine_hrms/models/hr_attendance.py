from odoo import models, fields, api
from odoo.exceptions import UserError


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    day_type = fields.Selection([
        ('weekday', 'Weekday'),
        ('weekend', 'Weekend'),
        ('public_holiday', 'Public Holiday')
    ], compute='_compute_day_type')
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id",
                                    readonly=True, store=True)

    is_ot_rate = fields.Boolean(copy=False)
    is_fixed_allowance = fields.Boolean(copy=False)
    is_emp_entry_created = fields.Boolean(default=False, copy=False)
    state = fields.Selection([
        ('draft', 'To Approve'),
        ('r1_approved', 'R1 Approved'), ('validation', 'Validated'),
        ('approved', 'Approved')
    ], string='Status', default='draft', tracking=True, copy=False, readonly=False,
    )

    @api.model
    def create(self, vals):
        res = super(HrAttendance, self).create(vals)
        employee_id = vals.get('employee_id')
        check_in = vals.get('check_in')
        if employee_id and check_in:
            contracts = self.env['hr.contract'].search([
                ('employee_id', '=', employee_id),
                ('date_start', '<=', check_in),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', check_in),
                ('is_fixed_allowance', '=', True),
            ])
            if contracts:
                res.is_fixed_allowance = True
        return res

    @api.depends('check_in')
    def _compute_day_type(self):
        for record in self:
            record.day_type = False
            if not record.check_in:
                continue
            check_in_date = record.check_in.date()
            public_holiday = self.env['resource.calendar.leaves'].search([
                ('date_from', '<=', record.check_in),
                ('date_to', '>=', record.check_in),
            ], limit=1)
            if public_holiday:
                record.day_type = 'public_holiday'
            else:
                day = record.check_in.weekday()
                record.day_type = 'weekend' if day >= 5 else 'weekday'

    def action_overtime_hour(self):
        for rec in self.browse(self.env.context.get('active_ids', [])):
            contract = self.env['hr.contract'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('date_start', '<=', rec.check_in),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', rec.check_in),
            ], limit=1)
            if not contract:
                raise UserError("No valid contract found for this employee!")
            if contract.ot_wage == 'monthly_fixed':
                if not contract.fixed_ot_allowance:
                    raise UserError("Monthly fixed OT allowance is not set in the contract!")
            elif contract.ot_wage == 'daily_fixed':
                if not contract.over_time:
                    raise UserError("Daily OT rate is not set in the contract!")
            elif contract.ot_wage == 'hourly_fixed':
                if not contract.hourly_ot_rate:
                    raise UserError("Hourly OT rate is not set in the contract!")
            else:
                raise UserError("OT Wage type is not configured in the contract!")

            rec.state = 'validation'

    @api.depends('worked_hours')
    def _compute_overtime_hours(self):
        att_progress_values = dict()
        if self.employee_id:
            self.env['hr.attendance'].flush_model(['worked_hours'])
            self.env['hr.attendance.overtime'].flush_model(['duration'])
            self.env.cr.execute('''
                WITH employee_time_zones AS (
                    SELECT employee.id AS employee_id,
                           calendar.tz AS timezone
                      FROM hr_employee employee
                INNER JOIN resource_calendar calendar
                        ON calendar.id = employee.resource_calendar_id
                )
                SELECT att.id AS att_id,
                       att.worked_hours AS att_wh,
                       ot.id AS ot_id,
                       ot.duration AS ot_d,
                       ot.date AS od,
                       att.check_in AS ad
                  FROM hr_attendance att
            INNER JOIN employee_time_zones etz
                    ON att.employee_id = etz.employee_id
            INNER JOIN hr_attendance_overtime ot
                    ON date_trunc('day',
                                  CAST(att.check_in
                                           AT TIME ZONE 'utc'
                                           AT TIME ZONE etz.timezone
                                  as date)) = date_trunc('day', ot.date)
                   AND att.employee_id = ot.employee_id
                   AND att.employee_id IN %s
              ORDER BY att.check_in DESC
            ''', (tuple(self.employee_id.ids),))
            a = self.env.cr.dictfetchall()
            grouped_dict = dict()
            for row in a:
                if row['ot_id'] and row['att_wh']:
                    if row['ot_id'] not in grouped_dict:
                        grouped_dict[row['ot_id']] = {'attendances': [(row['att_id'], row['att_wh'])], 'overtime_duration': row['ot_d']}
                    else:
                        grouped_dict[row['ot_id']]['attendances'].append((row['att_id'], row['att_wh']))

            for ot in grouped_dict:
                ot_bucket = grouped_dict[ot]['overtime_duration']
                for att in grouped_dict[ot]['attendances']:
                    if ot_bucket > 0:
                        sub_time = att[1] - ot_bucket
                        if sub_time < 0:
                            att_progress_values[att[0]] = 0
                            ot_bucket -= att[1]
                        else:
                            att_progress_values[att[0]] = float(((att[1] - ot_bucket) / att[1])*100)
                            ot_bucket = 0
                    else:
                        att_progress_values[att[0]] = 100
        for attendance in self:
            extra_hours = attendance.worked_hours * (
                    (100 - att_progress_values.get(attendance.id, 100)) / 100
            )

            attendance.overtime_hours = max(extra_hours, 0.0)
            # attendance.overtime_hours = attendance.worked_hours * ((100 - att_progress_values.get(attendance.id, 100))/100)

