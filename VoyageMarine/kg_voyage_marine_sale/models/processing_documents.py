from odoo import models, fields


class KGProcessingDocuments(models.Model):
    _name = "processing.documents"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Processing Documents"

    name = fields.Char(string="Name", required=True, copy=False)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    description = fields.Html(string="Description", copy=False)
    checklist_names = fields.Many2many("checklist.name", string="Checklists")
    is_default = fields.Boolean(string="Is Default")
