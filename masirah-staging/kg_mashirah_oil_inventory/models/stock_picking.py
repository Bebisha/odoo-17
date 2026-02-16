from odoo import models, api
from odoo.exceptions import ValidationError


class KGStockPickingInherit(models.Model):
    _inherit = "stock.picking"

    # def button_validate(self):
    #     for rec in self:
    #         if rec.picking_type_code == 'incoming' and rec.move_ids_without_package:
    #             for move_id in  rec.move_ids_without_package:
    #                 purchase_line = move_id.purchase_line_id
    #                 purchase_qty = purchase_line.product_qty if purchase_line else 0
    #                 received_qty = purchase_line.qty_received if purchase_line else 0
    #                 done_qty = move_id.quantity
    #                 total_qty_to_receive = purchase_qty -received_qty
    #                 if total_qty_to_receive > done_qty:
    #                     raise ValidationError("Received quantity cannot exceed the Ordered quantity.")
    #
    #         return super(KGStockPickingInherit, self).button_validate()

    @api.constrains('move_ids_without_package')
    def _check_grn_contain_po(self):
        for rec in self:
            if not rec.move_ids_without_package:
                raise ValidationError("Operation lines cannot be empty.")
            if rec.picking_type_code == 'incoming':
                for move_id in rec.move_ids_without_package:
                    if not move_id.purchase_line_id:
                        raise ValidationError("GRN can be created only from a PO.")
