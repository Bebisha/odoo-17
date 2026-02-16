from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class KGProductCategoryInherit(models.Model):
    _inherit = "product.category"

    code = fields.Char("Product Category Code")
    sequence_id = fields.Many2one('ir.sequence', 'Reference Sequence')

    @api.onchange('code')
    def change_category_code(self):
        for rec in self:
            if rec.code and rec.sequence_id:
                rec.sequence_id.prefix = rec.code

    def kg_create_sequence(self):
        product_category_id = self.env['product.category'].search([])
        if product_category_id:
            for rec in product_category_id:
                if not rec.sequence_id:
                    if rec.code:
                        rec.sequence_id = self.env['ir.sequence'].sudo().create({
                            'name': rec.name + ' ' + _('Sequence') + ' ' + rec.code,
                            'prefix': rec.code,
                            'padding': 3,
                            'company_id': False,
                        }).id

    @api.constrains('code')
    def check_product_code(self):
        for rec in self:
            if rec.code:
                if len(rec.code) != 2:
                    raise ValidationError(_("Product Category code should be 2 digits"))
            category_id = self.search([('code', '=', rec.code), ('id', '!=', self.id)])
            if category_id:
                raise ValidationError(_("Product Category code is unique"))
