# -*- coding: utf-8 -*-

from odoo import models, fields, api
# from odoo.addons.base.models.ir_actions_report import available
from odoo.exceptions import UserError, ValidationError


class InventoryUpdate(models.Model):
    _name = 'inventory.update'
    _description = 'Inventory Update'

    date = fields.Date(string='Date')
    batch_no = fields.Char(string='Batch Number')
    product_id = fields.Many2one('product.template', string='Product')
    location_id = fields.Many2one('res.country', string='Location')
    code = fields.Char(string='Code', related='product_id.default_code', store=True, readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    name = fields.Char(string='Description')
    label = fields.Char(string='Label')
    uom_id = fields.Many2one('uom.uom', string='Unit Of Measure')
    quantity = fields.Float(string='Quantity')
    kg = fields.Float(string='Kilograms', compute='compute_qty_in_kg', readonly=False)
    state = fields.Selection([('new', "New"), ('updated', "Updated")],
                             string="State", default='new')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel', related='warehouse_id.vessel_id', store=True)
    batch_id = fields.Many2one("stock.batch", string="Batch")

    @api.depends('quantity', 'uom_id')
    def compute_qty_in_kg(self):
        for update in self:
            ref_qty = update.uom_id.factor_inv

            update.write({
                'kg': update.quantity * ref_qty
            })

    def action_update(self):
        for update in self:
            if update.state == 'updated':
                raise UserError(
                    f"Stock for '{update.product_id.name}, {update.warehouse_id.name}, {update.date}' has already been updated.")
            vals = {
                'location_id': update.warehouse_id.lot_stock_id.id,
                'product_id': update.product_id.product_variant_id.id,
                'inventory_quantity': update.quantity,
                'stock_date': update.date,
                'batch_id': update.batch_id.id,
            }
            quant = self.env['stock.quant'].create(vals)
            quant.sudo().action_apply_inventory()
            quant.user_id = self.env.user.id
            if quant.user_id and quant.user_id.warehouse_id:
                warehouse_id = quant.user_id.warehouse_id
                user_ids = self.env['res.users'].search([('warehouse_id', '=', warehouse_id.id)])
                if user_ids:
                    quant.user_ids |= user_ids
            update.write({
                'state': 'updated',
            })

    def action_stock_return(self):
        for rec in self:
            if rec.state == 'new':
                raise ValidationError(
                    f"Stock for '{rec.product_id.name}, {rec.warehouse_id.name}, {rec.date}' has not been updated.")
            else:
                quant_ids = self.env['stock.quant'].search(
                    [('warehouse_id', '=', rec.warehouse_id.id), ('product_id', '=', rec.product_id.id),
                     ('location_id', '=', rec.warehouse_id.lot_stock_id.id)])
                if quant_ids:
                    available_qty = sum(quant_ids.mapped('quantity'))
                    if rec.quantity and available_qty:
                        if rec.quantity <= available_qty:
                            vals = {
                                'location_id': rec.warehouse_id.lot_stock_id.id,
                                'product_id': rec.product_id.product_variant_id.id,
                                'inventory_quantity': -rec.quantity,
                                'stock_date': rec.date,
                                'batch_id': rec.batch_id.id,
                            }
                            quant = self.env['stock.quant'].create(vals)
                            quant.sudo().action_apply_inventory()
                            quant.user_id = self.env.user.id
                            rec.state = 'new'
                        else:
                            raise ValidationError(
                                f"Stock for '{rec.product_id.name}, {rec.warehouse_id.name}, {rec.date}' is already out, so it cannot be returned.")
