from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    # is_subscription = fields.Boolean(
    #     string="Is a Subscription?",
    #     help="Enable this if the product is sold as a subscription."
    # )




class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_subscription = fields.Boolean(
        string="Is a Subscription",
        help="Enable this if the product is sold as a subscription."
    )