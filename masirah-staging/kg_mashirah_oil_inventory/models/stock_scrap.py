from ast import literal_eval

from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _


class KGStockScrapInherit(models.Model):
    _name = "stock.scrap"
    _inherit = ['stock.scrap', 'mail.activity.mixin', 'mail.thread']

    is_request = fields.Boolean(string="Is Request", default=False, copy=False)
    is_fm_approve = fields.Boolean(string="Is Finance Manager Approve", default=False, copy=False)
    is_stock_scrap_approve = fields.Boolean(string="Is Stock Scrap Approve", default=False, copy=False)
    is_reject = fields.Boolean(string="Is Reject", default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['is_request'] = True
            self._check_company()
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.scrap') or _('New')
        return super(KGStockScrapInherit, self).create(vals_list)

    def kg_request(self):
        fm_users = []

        fm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.finance_manager_ids', False)

        if not fm_approve_users or fm_approve_users == '[]':
            raise ValidationError(_("Please Select Finance Manager in Configuration"))

        if literal_eval(fm_approve_users):
            for i in literal_eval(fm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    fm_users.append(users)

            for user in fm_users:
                self.activity_schedule('kg_mashirah_oil_inventory.finance_manager_scrap_approval_notification',
                                       user_id=user.id,
                                       note=f' The User {self.env.user.name} request the Finance Manager to approve the Scrap Order {self.name}. Please Verify and approve.')
        self.is_fm_approve = True

    def kg_fm_approve(self):
        fm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.finance_manager_ids', False)

        if self.env.user.id not in literal_eval(fm_approve_users):
            raise UserError(_("You have no access to approve"))
        else:
            finance_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_inventory.finance_manager_scrap_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == finance_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == finance_manager_notification_activity)
            activity_2.action_done()

            fm_users = []

            if literal_eval(fm_approve_users):
                for i in literal_eval(fm_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        fm_users.append(users)

                for user in fm_users:
                    self.activity_schedule('kg_mashirah_oil_inventory.scrap_order_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the Finance Manager approval of the Scrap Order {self.name}.')

            scrap_approved_notification_activity = self.env.ref(
                'kg_mashirah_oil_inventory.scrap_order_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == scrap_approved_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == scrap_approved_notification_activity)
            activity_2.action_done()

            self.is_stock_scrap_approve = True

    def kg_reject(self):
        fm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.finance_manager_ids', False)

        if self.env.user.id not in literal_eval(fm_approve_users):
            raise UserError(_("You have no access to reject"))
        else:
            self.activity_schedule('kg_mashirah_oil_inventory.reject_scrap_order_notification',
                                   user_id=self.create_uid.id,
                                   note=f' The user {self.env.user.name}  has rejected the approval of the Scrap Order {self.name}.')

            reject_scrap_order_notification_activity = self.env.ref(
                'kg_mashirah_oil_inventory.reject_scrap_order_notification')
            activity = self.activity_ids.filtered(
                lambda l: l.activity_type_id == reject_scrap_order_notification_activity)
            activity.action_done()

            finance_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_inventory.finance_manager_scrap_approval_notification')
            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == finance_manager_notification_activity)
            activity_1.unlink()

            self.is_reject = True

    def action_validate(self):
        if self.is_reject:
            raise ValidationError("You cannot confirm because your request has been rejected")

        if not self.is_stock_scrap_approve:
            raise ValidationError("You cannot do this action without approval")

        return super(KGStockScrapInherit, self).action_validate()

    def do_scrap(self):
        self._check_company()
        for scrap in self:
            move = self.env['stock.move'].create(scrap._prepare_move_values())
            # master: replace context by cancel_backorder
            move.with_context(is_scrap=True)._action_done()
            scrap.write({'state': 'done'})
            scrap.date_done = fields.Datetime.now()
            if scrap.should_replenish:
                scrap.do_replenish()
        return True
