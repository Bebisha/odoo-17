
from odoo import models, fields, api, _


class ProjectType(models.Model):
    _inherit = 'project.task.type'

    is_open = fields.Boolean(string="Opening Stage")


