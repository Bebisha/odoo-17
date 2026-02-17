from odoo import models, fields, api

class AttendanceReport(models.Model):
    _name = 'kg.attendance.report'
    _description = "Model for Attendance Report"

    date = fields.Date('Date')
    company_id = fields.Many2one('res.company','Company')

    attendance_ids = fields.One2many('attendance.line','attendance_id','Report Line')

    @api.onchange('date','company_id')
    def _onchange_date_company(self):
        domain = []
        report_lines = []
        self.attendance_ids = False
        if self.date:
            domain.append(('date', '=', self.date),)
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))
        attendance_records = self.env['kg.attendance'].search(domain)
        if self.date and self.company_id:
            if attendance_records:
                for attendance in attendance_records:
                    for line in attendance.attendance_line_ids:
                        report_lines.append((0, 0, {
                            'employee_name': line.employee_name,
                            'employee_id': line.employee_id,
                            'time_in': line.time_in,
                            'time_out': line.time_out
                        }))
                self.attendance_ids = report_lines
