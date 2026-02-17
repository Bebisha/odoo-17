from odoo import models, fields, api, _
from odoo.tools import format_datetime, formatLang

class KGProductTemplate(models.Model):
    _inherit = "product.template"

    is_manufactured_product = fields.Boolean(string="Manufactured Product", help="Check this box if this is the master required for manufactured products.")
    is_discount_product = fields.Boolean(string="Discount Product")
    # is_discount_product = fields.Boolean(related='product_id.is_discount_product')

class KGProductProduct(models.Model):
    _inherit = "product.product"

    is_discount_product = fields.Boolean(string="Discount Product")