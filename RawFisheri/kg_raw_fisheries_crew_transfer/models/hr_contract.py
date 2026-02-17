from odoo import models, fields


class CrewContractInherit(models.Model):
    _inherit = "hr.contract"

    crew_transfer_ids = fields.Many2many("crew.transfer", string="Crew Transfers")
