# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_verified = fields.Boolean(string="Is Verified", copy=False)
    request_id = fields.Many2one('kg.material.request')

    def action_verified_all(self):
        for line in self.move_ids_without_package:
            line.is_verified = True
        self.is_verified = True

    def _create_backorder(self):
        backorders = super()._create_backorder()
        # 🛠 Now find moves that were just moved to the backorders and update their 'qty'
        for picking in backorders:
            picking.write({
                'is_request':False,
                'approved_by':False,
                'rejected_by':False
            })
            moves = picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
            moves.write({'qty': 0})

        return backorders

    def button_validate(self):
        for picking in self:
            if picking.picking_type_code == 'outgoing':
                if any(not line.is_verified for line in picking.move_ids_without_package):
                    raise UserError(_('Not all lines have been verified yet!'))
                for move in picking.move_ids_without_package:
                    product = move.product_id
                    qty_needed = move.qty
                    # product_packaging_qty = move.qty
                    available_qty = product.with_context({'location': picking.location_id.id}).qty_available

                    if qty_needed > available_qty:
                        raise UserError(
                            f"Not enough stock for product '{product.display_name}'.\n"
                            f"Requested: {qty_needed} {move.product_uom.name}, "
                            f"Available: {available_qty} {product.uom_id.name}'."
                        )

            if picking.picking_type_code == 'incoming':
                for move in picking.move_ids_without_package:
                    # if move.productoduct_uom_qty>move.qty:
                        move.action_verified()

        res = super(StockPicking, self).button_validate()
        return res

    def action_update_quantity(self):
        return {
            'name': _('Update Quantity'),
            'type': 'ir.actions.act_window',
            'res_model': 'update.quantity.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_update_id': self.id,
            }
        }
    is_request = fields.Boolean(string="Is Request", default=False)
    is_approve = fields.Boolean(string="Is Approved", default=False)
    is_reject = fields.Boolean(string="Is Reject", default=False)
    reject_reason = fields.Text(string="Reject Reason")
    rejected_by = fields.Many2one('res.users', string="Rejected By", readonly=True)
    approved_by = fields.Many2one('res.users', string="Approved By", readonly=True)

    def kg_request_approve(self):

        for record in self:
            record.is_request = True
            # record.state = 'request'
            for move in record.move_ids_without_package:
                if not move.qty:
                    raise UserError("Please Enter the Entered Quantity.")
            approval_group = self.env.ref('kg_material_request.receipt_approval_group_user')
            users = approval_group.users
            # if not users:
            #     raise UserError("No users found in the approval group.")

            sender_name = self.env.user.partner_id.name
            sender_email = self.env.user.email_formatted

            mail_values = {
                'subject': f'Approval Requested for Receipt {record.name}',
                'body_html': f'''
                    <p>Dear,</p>
                    <p><strong>{sender_name}</strong> has requested approval for a stock picking receipt.</p>
                    <p><strong>Receipt Reference:</strong> {record.name}</p>
                    <p><strong>Scheduled Date:</strong> {record.scheduled_date.strftime('%Y-%m-%d') if record.scheduled_date else 'N/A'}</p>
                    <p>Please review it in the system.</p>
                ''',
                'email_from': sender_email,
                'recipient_ids': [(4, user.partner_id.id) for user in users if user.partner_id.email],
            }

            self.env['mail.mail'].create(mail_values).send()

    def action_stock_approve(self):

        for record in self:
            record.is_approve = True
            record.move_ids_without_package.write({'is_verified': True})
            requester = record.create_uid.partner_id
            approver = self.env.user.partner_id
            record.approved_by = self.env.user

            if not requester.email:
                raise UserError("The requester does not have an email address.")

            mail_values = {
                'subject': f'Receipt {record.name} Approved',
                'body_html': f'''
                    <p>Hello {requester.name},</p>
                    <p>Dear,</p>
                    <p>Your request for stock picking approval has been <strong>approved</strong>.</p>
                    <p><strong>Receipt Reference:</strong> {record.name}</p>
                    <p><strong>Approved By:</strong> {approver.name}</p>
                    <p>You may proceed with further actions.</p>
                ''',
                'email_from': approver.email_formatted,
                'recipient_ids': [(4, requester.id)],
            }

            self.env['mail.mail'].create(mail_values).send()

    def action_reject_receipt(self):
        return {
            'name': _('Reject Reason'),
            'type': 'ir.actions.act_window',
            'res_model': 'rejects.reason.receipt',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_receipt_id': self.id,
            }
        }


class AccountMovelLine(models.Model):
    _inherit = "account.move.line"

    default_code = fields.Char(string="Part code", related='product_id.default_code')


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    hide_qty = fields.Boolean(
        string="Show Quantity",
        compute='_compute_show_quantity',
        store=True,
    )

    # @api.depends('uid')
    def _compute_show_quantity(self):
        for record in self:
            record.hide_qty = self.env.user.has_group('stock.group_stock_manager')


    @api.model
    def action_view_inventory(self):
        """Custom override to use a different tree view for restricted users."""
        # Call the super to get the standard action
        action = super().action_view_inventory()

        # Check if user is in the custom restricted group
        if self.env.user.has_group('kg_material_request.group_stock_user_restricted'):
            # Replace the view_id with your restricted view
            action['view_id'] = self.env.ref('kg_material_request.view_stock_quant_tree_inventory_editable_qty').id

        return action
