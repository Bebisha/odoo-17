from odoo import fields, models

class KGCRMStage(models.Model):
    _inherit = "crm.stage"

    is_opportunity = fields.Boolean('Is Opportunity?', copy=False)