from datetime import date

from odoo import models, fields, api
from odoo.exceptions import UserError


class OrderLineWizard(models.TransientModel):
    _name = 'order.line.wizard'
    _description = 'Wizard for Selecting Order Lines'

    order_line_ids = fields.One2many('order.line.wizard.line', 'wizard_id', string="Order Lines")
    all_products_created = fields.Boolean(string="All Products Created", compute="_compute_all_products_created",
                                          store=True)

    @api.depends('order_line_ids.product_created')
    def _compute_all_products_created(self):
        """Check if all lines have products created."""
        for wizard in self:
            wizard.all_products_created = all(wizard.order_line_ids.mapped('product_created'))

    def action_create_all_products(self):

        for line in self.order_line_ids.filtered(lambda l: not l.product_created):
            if not line.product_group_id:
                raise UserError(f"Product Group is required for Order Line {line.order_line_id.name}.")
            if not line.category_id:
                raise UserError(f"Category is required for Order Line {line.order_line_id.name}.")
            product = self.env['product.product'].create({
                'name': line.name,
                'type': 'product',
                'default_code': line.order_line_id.code or '',
                'categ_id': line.category_id.id or '',
                'product_group_id': line.product_group_id.id or '',
            })
            line.order_line_id.product_id = product.id
            line.product_created = True
        return {'type': 'ir.actions.client', 'tag': 'reload'}


class OrderLineWizardLine(models.TransientModel):
    _name = 'order.line.wizard.line'
    _description = 'Wizard Order Line'

    wizard_id = fields.Many2one('order.line.wizard', string="Wizard")
    order_line_id = fields.Many2one('sale.order.line', string="Order Line", required=True)
    name = fields.Char(string="Product Name", compute="_compute_name", store=True)
    product_group_id = fields.Many2one("product.group", string="Product Group")
    category_id = fields.Many2one("product.category", string="Category")
    product_created = fields.Boolean(string="Product Created", default=False)

    @api.depends('order_line_id')
    def _compute_name(self):
        for record in self:
            record.name = record.order_line_id.name if record.order_line_id else ''

    def action_create_product(self):
        if not self.product_group_id:
            raise UserError("Product Group is required to create a product.")
        if not self.category_id:
            raise UserError("Category is required to create a product.")
        """Create a product from the order line and assign to product_id."""
        for record in self:
            if record.order_line_id:
                product = self.env['product.product'].create({
                    'name': record.name,
                    'type': 'product',
                    'categ_id': record.category_id.id or '',
                    'product_group_id': record.product_group_id.id or '',
                    'default_code': record.order_line_id.code or '',
                })
                record.order_line_id.product_id = product.id
                record.product_created = True
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'product.product',
                    'view_mode': 'form',
                    'res_id': product.id,
                    'target': 'current',
                }


