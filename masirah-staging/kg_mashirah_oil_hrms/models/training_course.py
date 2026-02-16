from odoo import models, fields


class TrainingCourse(models.Model):
    _name = "training.course"
    _description = "Employee Training Course"
    _inherit = ['mail.thread']

    name = fields.Char(string="Course Name")
