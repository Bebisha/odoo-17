# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    show_part_code = fields.Boolean("Show Part Code in Print")

    def action_create_invoice(self):
        for order in self:
            if not order.partner_id.bank_ids:
                raise ValidationError(_(
                    "Unable to create a bill for Purchase Order '%s' as the vendor '%s' does not have a bank account configured."
                ) % (order.name, order.partner_id.name))
        return super(PurchaseOrder, self).action_create_invoice()

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals['kg_lpo'] = self.name
        return invoice_vals


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    default_code = fields.Char(string="Part code", related='product_id.default_code')

    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        super()._get_product_purchase_description(product_lang)
        return product_lang.name

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        res = super()._prepare_account_move_line(move)
        res['name'] = self.name
        return res


# class AccountMove(models.Model):
#     _inherit = "account.move"
#
#     def action_post(self):
#         res = super().action_post()
#         for move in self:
#                 move.ref = move.name
#         return res
