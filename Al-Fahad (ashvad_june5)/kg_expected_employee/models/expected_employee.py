from odoo import api, fields, models, _


class EmployeeForm(models.Model):
    _name = 'expected.employee'
    _rec_name = 'emp_name'

    emp_name = fields.Char(string="Employee Name", required=True)
    department = fields.Many2one('employee.department', string="Department")
    emp_reg = fields.Integer(string="Employee Number")
