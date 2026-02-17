from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = 'Request For Quotation'

    location_dest_id = fields.Many2one(
        comodel_name="stock.location",
        string="Destination Location", related="mr_dest_loc_id"
    )

    mr_dest_loc_id = fields.Many2one("stock.location", compute="compute_mr_dest_loc")

    def compute_mr_dest_loc(self):
        for rec in self:
            if rec.requisition_po_id:
                mr_id = self.env['material.purchase.requisition'].search([('id', '=', rec.requisition_po_id.id)],
                                                                         limit=1)
                if mr_id and mr_id.department_res_id and mr_id.department_res_id.destination_location_id:
                    rec.mr_dest_loc_id = mr_id.department_res_id.destination_location_id.id
                else:
                    rec.mr_dest_loc_id = False
            else:
                rec.mr_dest_loc_id = False

    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res[
            'location_dest_id'] = self.location_dest_id.id if self.location_dest_id else self._get_destination_location()
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    location_dest_id = fields.Many2one(
        comodel_name="stock.location",
        string="Destination Location", related="mr_dest_loc_id"
    )
    mr_dest_loc_id = fields.Many2one("stock.location", compute="compute_mr_dest_loc")

    def compute_mr_dest_loc(self):
        for rec in self:
            if rec.order_id and rec.order_id.requisition_po_id:
                mr_id = self.env['material.purchase.requisition'].search(
                    [('id', '=', rec.order_id.requisition_po_id.id)],
                    limit=1)
                if mr_id and mr_id.department_res_id and mr_id.department_res_id.destination_location_id:
                    rec.mr_dest_loc_id = mr_id.department_res_id.destination_location_id.id
                else:
                    rec.mr_dest_loc_id = False
            else:
                rec.mr_dest_loc_id = False

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(PurchaseOrderLine,self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        if self.location_dest_id:
            res['location_dest_id'] = self.location_dest_id.id
        elif self.orderpoint_id and not (self.move_ids | self.move_dest_ids):
            picking_location_path = picking.location_dest_id.parent_path
            orderpoint_location_path = self.orderpoint_id.location_id.parent_path
            if picking_location_path in orderpoint_location_path:
                res['location_dest_id'] = self.orderpoint_id.location_id.id
            else:
                res['location_dest_id'] = self.order_id._get_destination_location()
        else:
            res['location_dest_id'] = self.order_id._get_destination_location()

        return res

