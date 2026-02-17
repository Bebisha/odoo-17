from odoo import models, fields

class KGBrand(models.Model):
    _name="product.brand"
    _description = "Brands"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    code = fields.Char(string=" New Code")
    old_code = fields.Char(string="Old Code")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

