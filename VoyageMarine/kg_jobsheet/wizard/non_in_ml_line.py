from datetime import date

from odoo import models, fields, api
from odoo.exceptions import UserError



class OrderLineWizardLine(models.TransientModel):
    _inherit = 'order.line.wizard.line'
    _description = 'Wizard Order Line'

    product_group_id = fields.Many2one("product.group", string="Product Group")
    category_id = fields.Many2one("product.category", string="Category")

