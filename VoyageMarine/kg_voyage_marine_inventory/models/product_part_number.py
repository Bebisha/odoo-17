from odoo import models, fields, api


class ProductPartNumberSequence(models.Model):
    _name = 'product.part.number.sequence'
    _description = 'Product Part Number Sequence'

    name = fields.Char(string="Reference")
    category_id = fields.Many2one("product.category", string="Category" )
    subcategory_id = fields.Many2one("sub.category", string="Sub Category")
    brand_id = fields.Many2one("product.brand", string="Brand")
    current_sequence = fields.Integer(string="Current Sequence", default=1)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)

    @api.depends('category_id', 'subcategory_id', 'brand_id', 'current_sequence')
    def _compute_display_name(self):
        for rec in self:
            if rec.category_id and rec.subcategory_id and rec.brand_id and rec.current_sequence:
                rec.display_name = f"{rec.category_id.code}/{rec.subcategory_id.code}/{rec.brand_id.code}/{rec.current_sequence}"
            else:
                rec.display_name = False