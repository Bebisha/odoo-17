from odoo import models, fields, api, _
from ast import literal_eval
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class KGAccountPaymentInherit(models.Model):
    _inherit = "account.payment"

    is_request = fields.Boolean(string="Is Request", default=False, copy=False)
    is_bill_approve = fields.Boolean(string="Is RFQ Approve", default=False, copy=False)
    is_reject = fields.Boolean(string="Is Reject", default=False, copy=False)
    is_fm_approve = fields.Boolean(string="Is Finance Manager Approve", default=False, copy=False)
    is_gm_approve = fields.Boolean(string="Is General Manager Approve", default=False, copy=False)

    finance_manager = fields.Many2one('res.users')
    general_manager = fields.Many2one('res.users')

    def kg_request(self):
        fm_users = []

        fm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.finance_manager_ids', self.finance_manager)

        if literal_eval(fm_approve_users):
            for i in literal_eval(fm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    fm_users.append(users)

            for user in fm_users:
                self.activity_schedule('kg_mashirah_oil_accounting.finance_manager_approval_notification',
                                       user_id=user.id,
                                       note=f' The User {self.env.user.name} request the Finance Manager to approve the Vendor Bills {self.name}. Please Verify and approve.')

        self.is_request = True
        self.is_fm_approve = True

    def kg_fm_approve(self):

        finance_manager_approval_notification_activity = self.env.ref(
            'kg_mashirah_oil_accounting.finance_manager_approval_notification')

        activity_1 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == finance_manager_approval_notification_activity)
        not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

        for ccc in not_current_user_confirm:
            ccc.unlink()

        activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == finance_manager_approval_notification_activity)
        activity_2.action_done()

        gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.general_manager_ids', self.general_manager)

        gm_users = []

        if literal_eval(gm_approve_users):
            for i in literal_eval(gm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    gm_users.append(users)

            for user in gm_users:
                self.activity_schedule('kg_mashirah_oil_accounting.general_manager_approval_notification',
                                       user_id=user.id,
                                       note=f' The user {self.env.user.name} has approved the Finance Manager approval and request the GM to approve the Vendor Bill {self.name}. Please Verify and approve.')
        self.is_fm_approve = False
        self.is_gm_approve = True

    def kg_reject(self):
        self.activity_schedule('kg_mashirah_oil_accounting.reject_vendor_bill_notification',

                               note=f' The user {self.env.user.name}  has rejected the approval of the Vendor Bill {self.name}.')

        reject_vendor_bill_notification_activity = self.env.ref(
            'kg_mashirah_oil_accounting.reject_vendor_bill_notification')
        activity = self.activity_ids.filtered(
            lambda l: l.activity_type_id == reject_vendor_bill_notification_activity)
        activity.action_done()

        finance_manager_approval_notification_activity = self.env.ref(
            'kg_mashirah_oil_accounting.finance_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == finance_manager_approval_notification_activity)
        activity_1.unlink()

        general_manager_notification_activity = self.env.ref(
            'kg_mashirah_oil_accounting.general_manager_approval_notification')
        activity_2 = self.activity_ids.filtered(lambda l: l.activity_type_id == general_manager_notification_activity)
        activity_2.unlink()

        self.is_reject = True
        self.is_request = False
        self.is_fm_approve = False
        self.is_gm_approve = False
        self.is_bill_approve = False

    def button_draft(self):
        res = super(KGAccountPaymentInherit, self).button_draft()
        self.is_reject = False
        self.is_request = True
        self.is_fm_approve = True
        self.is_gm_approve = False
        self.is_bill_approve = False

        return res

    def kg_gm_approve(self):
        gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.general_manager_ids', self.general_manager)

        gm_users = []
        general_manager_notification_activity = self.env.ref(
            'kg_mashirah_oil_accounting.general_manager_approval_notification')

        activity_1 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == general_manager_notification_activity)
        not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

        for ccc in not_current_user_confirm:
            ccc.unlink()

        activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == general_manager_notification_activity)
        activity_2.action_done()

        if literal_eval(gm_approve_users):
            for i in literal_eval(gm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    gm_users.append(users)

            for user in gm_users:
                self.activity_schedule('kg_mashirah_oil_accounting.vendor_bill_approval_notification',
                                       user_id=user.id,
                                       note=f' The user {self.env.user.name} has approved the GM approval of the Vendor Bill {self.name}.')

        vendor_bill_approval_notification_activity = self.env.ref(
            'kg_mashirah_oil_accounting.vendor_bill_approval_notification')

        activity_1 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == vendor_bill_approval_notification_activity)
        not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

        for ccc in not_current_user_confirm:
            ccc.unlink()

        activity_2 = self.activity_ids.filtered(
            lambda l: l.activity_type_id == vendor_bill_approval_notification_activity)
        activity_2.action_done()

        self.is_gm_approve = False
        self.is_bill_approve = True
        self.action_post()


class KGAccountMoveInherit(models.Model):
    _inherit = "account.move"

    vendor_bill_id = fields.Many2one('account.payment', string="Vendor Bill id")
    hide_bool = fields.Boolean()

    def get_vendor_payment(self):
        self.ensure_one()

        return {
            'name': 'Vendor Payment',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'res_id': self.vendor_bill_id.id,
            # 'domain': [('id', '=', self.payment_id.id)],
            'type': 'ir.actions.act_window',
            'target': 'current',
        }


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.model
    def create(self, vals):
        account = super(AccountAccount, self).create(vals)

        if not self._context.get('creating_journal_entry'):
            journal_entry = self.env['account.move'].with_context(creating_journal_entry=True).create({
                'move_type': 'entry',
                'hide_bool': True,
                'date': fields.Date.today(),
                'line_ids': [(0, 0, {
                    'account_id': account.id,
                    'name': 'Initial Balance',
                    'debit': 0.0,
                    'credit': 0.0,
                })],
            })

        return account
