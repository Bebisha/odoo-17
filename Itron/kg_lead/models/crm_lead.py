from odoo import fields, models

class CrmLead(models.Model):
    _inherit = "crm.lead"

    is_change_req = fields.Boolean("Is Change Request", default=False)
    total_effort = fields.Float("Total Effort", copy=False)