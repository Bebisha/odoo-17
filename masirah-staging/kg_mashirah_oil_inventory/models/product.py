from odoo import models, fields, api, _


class KGProductTemplateInherit(models.Model):
    _inherit = "product.template"

    category_code = fields.Char("Product Category Code", related='categ_id.code')
    grade = fields.Char(string="Grade")
    avg_length = fields.Float(string="Avg.Length")
    serial_no = fields.Char(string="Serial No")
    mt_certificate_no = fields.Char(string="MT Certificate Number")
    usage = fields.Selection(
        [('in_use', 'In Use'), ('not_used_now', 'Not used as of now'), ('not_inventory', 'Not in inventory')],
        default='in_use', string="Usage")

    def kg_update_product_code(self):
        product_id = self.env['product.template'].search([])
        if product_id:
            for rec in product_id:
                if not rec.default_code:
                    if rec.categ_id and rec.categ_id.sequence_id:
                        rec.default_code = rec.categ_id.sequence_id.next_by_id()


class KGProductProductInherit(models.Model):
    _inherit = "product.product"

    category_code = fields.Char("Product Category Code", related='product_tmpl_id.category_code')
    grade = fields.Char(string="Grade", related='product_tmpl_id.grade')
    avg_length = fields.Float(string="Avg.Length", related='product_tmpl_id.avg_length')
    serial_no = fields.Char(string="Serial No", related="product_tmpl_id.serial_no")
    mt_certificate_no = fields.Char(string="MT Certificate Number", related="product_tmpl_id.mt_certificate_no")
    usage = fields.Selection(
        [('in_use', 'In Use'), ('not_used_now', 'Not used as of now'), ('not_inventory', 'Not in inventory')],
        related="product_tmpl_id.usage", string="Usage")
