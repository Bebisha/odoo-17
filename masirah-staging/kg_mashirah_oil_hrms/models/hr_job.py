from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'hr.job'

    grade_id = fields.Many2one('job.grade', 'Job Grade')
