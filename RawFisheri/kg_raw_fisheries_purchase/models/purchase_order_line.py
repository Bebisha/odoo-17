from odoo import models, fields


class KGPOLine(models.Model):
    _inherit = "purchase.order.line"

    product_image = fields.Image("Image", related="product_id.image_1920")
