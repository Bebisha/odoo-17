from odoo import models, fields


class KGHRJobInherit(models.Model):
    _inherit = "hr.job"

    code = fields.Char(string="Designation Code")