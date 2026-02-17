from odoo import models, fields

class ProjectProject(models.Model):
    _inherit = 'project.project'

    vessel_id = fields.Many2one("vessel.code", string="Vessel", related="sale_order_id.vessel_id", store=True)


