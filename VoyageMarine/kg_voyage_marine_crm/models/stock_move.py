from collections import defaultdict
from datetime import time, datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    physical_status_id = fields.Many2one('physical.status', string="Physical Status")
    accesories = fields.Text(string="Accessories")
    model = fields.Char(string='Model', )
    make = fields.Char(string="Make", )
    make_id = fields.Many2one('rec.make', string='Make')
    model_id = fields.Many2one('rec.model', string='Model')
    remark = fields.Text(string='Remark', copy=False)
    lead_id = fields.Many2one('crm.lead',string="CRM")

    def create(self, vals):
        """
        Supports both single dict and list of dict (vals_list).
        Automatically sets owner_id = move.lead_id.partner_id.id
        """
        # Normalize vals → always work with a list
        if isinstance(vals, dict):
            vals_list = [vals]
        else:
            vals_list = vals

        for val in vals_list:
            move_id = val.get('move_id')
            if move_id:
                move = self.env['stock.move'].browse(move_id)
                if move.exists() and move.lead_id and move.lead_id.partner_id:
                    val['owner_id'] = move.lead_id.partner_id.id
                else:
                    # No partner associated → do nothing
                    pass

        # Create records
        return super(StockMoveLine, self).create(vals_list)

    def _synchronize_quant(self, quantity, location, action="available", in_date=False, **quants_value):
        """ quantity should be express in product's UoM"""
        lot = quants_value.get('lot', self.lot_id)
        package = quants_value.get('package', self.package_id)
        owner = quants_value.get('owner', self.owner_id)
        self.lead_id = self.move_id.lead_id.id if self.move_id.lead_id else False
        print("ttttttttttttttttttttttttttttt")

        available_qty = 0
        if self.product_id.type != 'product' or float_is_zero(quantity, precision_rounding=self.product_uom_id.rounding):
            return 0, False
        if action == "available":
            available_qty, in_date = self.env['stock.quant']._update_available_quantity(self.product_id, location, quantity, lot_id=lot, package_id=package, owner_id=owner, in_date=in_date,physical_status_id=self.physical_status_id,make_id=self.make_id,model_id=self.model_id,accesories=self.accesories,lead_id=self.move_id.lead_id,remark=self.remark)
        elif action == "reserved" and not self.move_id._should_bypass_reservation(location):
            self.env['stock.quant']._update_reserved_quantity(self.product_id, location, quantity, lot_id=lot, package_id=package, owner_id=owner)
        print("jjjjjjjjjjjjjjjjjjjjj")
        if available_qty < 0 and lot:
            print("kkkkkkkkkkkkkkkkkkk")
            # see if we can compensate the negative quants with some untracked quants
            untracked_qty = self.env['stock.quant']._get_available_quantity(self.product_id, location, lot_id=False, package_id=package, owner_id=owner, strict=True)
            print(untracked_qty,"untracked_qty")
            if not untracked_qty:
                return available_qty, in_date
            taken_from_untracked_qty = min(untracked_qty, abs(quantity))
            self.env['stock.quant']._update_available_quantity(self.product_id, location, -taken_from_untracked_qty, lot_id=False, package_id=package, owner_id=owner, in_date=in_date,physical_status_id=self.physical_status_id,make_id=self.make_id,model_id=self.model_id,accesories=self.accesories,lead_id=self.move_id.lead_id,remark=self.remark)
            self.env['stock.quant']._update_available_quantity(self.product_id, location, taken_from_untracked_qty, lot_id=lot, package_id=package, owner_id=owner, in_date=in_date,physical_status_id=self.physical_status_id,make_id=self.make_id,model_id=self.model_id,accesories=self.accesories,lead_id=self.move_id.lead_id,remark=self.remark)
        print(available_qty,in_date,"kkkkkkkkkkkkkkkkkkkkkin_date")
        return available_qty, in_date

    def _action_assign(self, force_qty=False):
        """ Assign the lot_id present on the SO line to the stock move lines for rental orders. """
        super()._action_assign(force_qty=force_qty)

        for product in self.product_id:
            if not product.tracking == 'serial':
                continue
            moves = self.filtered(lambda m: m.product_id == product)
            sale_lines = self.env['sale.order.line']
            for move in moves:
                sale_lines |= move._get_sale_order_lines()

            if sale_lines.reserved_lot_ids:
                free_reserved_lots = sale_lines.reserved_lot_ids.filtered(lambda s: s not in moves.move_line_ids.lot_id)
                to_assign_move_lines = moves.move_line_ids.filtered(
                    lambda l: l.lot_id not in sale_lines.reserved_lot_ids)
                for line, lot in zip(to_assign_move_lines, free_reserved_lots):
                    line.lot_id = lot

class StockMove(models.Model):
    _inherit = "stock.move"

    lead_id = fields.Many2one('crm.lead', string="CRM")


class KGPicking(models.Model):
    _inherit = "stock.picking"

    lead_id = fields.Many2one('crm.lead', string="CRM")
    virtual_location_id = fields.Many2one(
        'stock.location',
        string="Destination Location",
    )

    # @api.onchange('virtual_location_id')
    # def _onchange_virtual_location_id(self):
    #     if self.virtual_location_id:
    #         self.location_dest_id = self.virtual_location_id.id
    #     else:
    #         self.location_dest_id = False

    # @api.model
    # def create(self, vals):
    #     if vals.get('virtual_location_id'):
    #         vals['location_dest_id'] = vals['virtual_location_id']
    #     return super().create(vals)
    #
    # def write(self, vals):
    #     if vals.get('virtual_location_id'):
    #         vals['location_dest_id'] = vals['virtual_location_id']
    #     return super().write(vals)
