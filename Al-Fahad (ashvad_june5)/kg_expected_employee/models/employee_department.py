from odoo import api, fields, models, _


class EmployeeDepartment(models.Model):
    _name = 'employee.department'
    _rec_name = 'dept_name'

    dept_name = fields.Char(string="Department Name",required=True)
    manager = fields.Many2one('res.users',string="Technical Assistant")

