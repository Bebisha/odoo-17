from odoo import models, fields, api, _



class KgStandardUsed(models.Model):
    _name = 'standard.used'
    _rec_name = 'display_name'

    @api.depends('name', 'scope_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.scope_id:
                rec.display_name = f"{rec.name} - {rec.scope_id.name}"

    display_name = fields.Char(compute='_compute_display_name')
    name = fields.Char(string="Standard Used")
    scope_id = fields.Many2one('product.category', string="Scope")
    product_category_id = fields.Many2one('product.category', string="Equipment Category")
