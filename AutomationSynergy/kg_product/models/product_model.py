from odoo import fields, models


class ProductsModel(models.Model):
    _name = 'product.model'
    _description = 'Product Model'


    name = fields.Char('Name')