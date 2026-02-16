from odoo import models, fields


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    offshore = fields.Boolean("Offshore")
