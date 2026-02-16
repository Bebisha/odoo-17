from odoo import models, fields


class ProductEnquiry(models.Model):
    _name = 'product.enquiry'
    _description = 'Product Enquiry'

    product_id = fields.Many2one('product.template', string="Product", required=True)
    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Email", required=True)
    phone = fields.Char(string="Contact Num", required=True)
    message = fields.Text(string="Message", required=True)
