from odoo import models, fields

class KGSubcategory(models.Model):
    _name="sub.category"
    _description = "Subcategory"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

