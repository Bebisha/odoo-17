from ast import literal_eval
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class KGPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    deliver_to_location = fields.Many2one("stock.location", string="Deliver to Location")
    inspection = fields.Char(string="Inspection")
    qa_condition = fields.Html(string="QA Condition")
    requested_by = fields.Many2one("res.users", string="Requested By")
    verified_by = fields.Many2one("res.users", string="Verified By")
    approved_by = fields.Many2one("res.users", string="Approved by")
    current_date = fields.Date(string='Current Date', default=fields.Date.today())

    is_request = fields.Boolean(string="Is Request", default=False, copy=False)
    is_pm_approve = fields.Boolean(string="Is Purchase Manager Approve", default=False, copy=False)
    is_gm_approve = fields.Boolean(string="Is General Manager Approve", default=False, copy=False)
    is_rfq_approve = fields.Boolean(string="Is RFQ Approve", default=False, copy=False)
    is_reject = fields.Boolean(string="Is Reject", default=False, copy=False)

    purchase_manager = fields.Many2one('res.users')
    general_manager = fields.Many2one('res.users')
    purchase_contract_id = fields.Many2one("purchase.contract.agreement", string="Purchase Contract")

    company_currency_id = fields.Many2one(string='Company Currency', readonly=True,
                                          related='company_id.currency_id')
    amount_in_currency = fields.Monetary(string="Amount in Currency(USD)", compute="convert_amount_in_currency",
                                         currency_field='company_currency_id')

    po_type = fields.Selection([('serv', 'Service'), ('matr', 'Material'), ('serv_and_matr', 'Service& Material')],
                               default='matr', string="Purchase Type")
    number_rfq = fields.Char('Quote No.', copy=False)
    # project_analytic_account_id = fields.Many2one('account.analytic.account', string="Project"  ,compute='_compute_analytic_distribution',)
    remarks = fields.Char('Remarks')


    @api.depends('amount_total', 'currency_id')
    def convert_amount_in_currency(self):
        for rec in self:
            if rec.currency_id != self.env.company.currency_id:
                converted_amount = rec.currency_id._convert(
                    rec.amount_total, self.env.company.currency_id, self.env.company,
                    rec.date_order.date()
                )
                rec.amount_in_currency = converted_amount
            else:
                rec.amount_in_currency = rec.amount_total

    @api.model_create_multi
    def create(self, vals_list):
        # This list will store the updated values that will be passed to the super method.
        updated_vals_list = []

        for i in vals_list:
            if i.get('is_check'):
                if i.get('revision_id'):
                    # If it's a revision and not yet a revision (is_revision is False)
                    if not i.get('is_revision'):
                        purchase_id = self.env['purchase.order'].search([('revision_id', '=', i['revision_id'])])
                        if purchase_id:
                            revision_seq = str(purchase_id[-1].name) + str('-R') + str(i['revision_count'] + 1)
                            update_seq = {
                                'name': revision_seq,
                                'is_revision': True
                            }
                            i.update(update_seq)
                    # If it's a revision and is_revision is True
                    else:
                        purchase_id = self.env['purchase.order'].search(
                            [('revision_id', '=', i['revision_id']), ('state', '=', 'cancel')])
                        if purchase_id:
                            revision_seq = str(purchase_id[-1].name) + str('-R') + str(i['revision_count'] + 1)
                            update_seq = {
                                'name': revision_seq,
                            }
                            i.update(update_seq)
            else:
                # Handle the case where 'is_check' is not present
                if i.get('name', 'New') == 'New' and i.get('state', 'draft') in ('draft', 'sent'):
                    rfq_seq = self.env['ir.sequence'].next_by_code('kg.purchase.rfq') or 'New'
                    # order.number_rfq = order.name
                    update_seq = {
                        'name': rfq_seq,
                        'is_request': True,
                        'number_rfq': rfq_seq
                    }
                    i.update(update_seq)

            # Append the updated values to the list
            updated_vals_list.append(i)

        return super(KGPurchaseOrder, self).create(updated_vals_list)

    project_analytic_account_id = fields.Many2one('account.analytic.account', string="Project",
                                                   )
    analytic_distribution = fields.Json(string="Analytic Distribution", compute='_compute_analytic_distribution',
                                        store=True)

    @api.depends('project_analytic_account_id', 'order_line')
    def _compute_analytic_distribution(self):
        for record in self:
            if record.project_analytic_account_id:
                analytic_id = record.project_analytic_account_id.id
                distribution = {analytic_id: 100}

                # Update the parent record's field
                record.analytic_distribution = distribution

                # Update related order lines
                for line in record.order_line:
                    line.write({'analytic_distribution': distribution})

    def kg_request(self):
        pm_users = []

        pm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.purchase_manager_ids', False)

        if not pm_approve_users or pm_approve_users == '[]':
            raise ValidationError(_("Please Select Purchase Manager in Configuration"))

        gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.general_manager_ids', False)

        if not gm_approve_users or gm_approve_users == '[]':
            raise ValidationError(_("Please Select General Manager in Configuration"))

        if literal_eval(pm_approve_users):
            for i in literal_eval(pm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    pm_users.append(users)

            for user in pm_users:
                self.activity_schedule('kg_mashirah_oil_purchase.purchase_manager_approval_notification',
                                       user_id=user.id,
                                       note=f' The User {self.env.user.name} request the Purchase Manager to approve the Purchase Order {self.name}. Please Verify and approve.')

        self.requested_by = self.env.user.id
        self.is_pm_approve = True

    def kg_pm_approve(self):
        print("opopopopo")

        pm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.purchase_manager_ids', False)

        if self.env.user.id not in literal_eval(pm_approve_users):
            raise UserError(_("You have no access to approve"))

        else:
            purchase_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_purchase.purchase_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == purchase_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == purchase_manager_notification_activity)
            activity_2.action_done()

            gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.general_manager_ids', False)

            gm_users = []

            if literal_eval(gm_approve_users):
                for i in literal_eval(gm_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        gm_users.append(users)

                for user in gm_users:
                    self.activity_schedule('kg_mashirah_oil_purchase.general_manager_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the Purchase Manager approval and request the GM to approve the Purchase Order {self.name}. Please Verify and approve.')

            self.verified_by = self.env.user.id
            self.is_gm_approve = True


    def kg_reject(self):
        if not self.is_gm_approve:
            pm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.purchase_manager_ids', False)

            if self.env.user.id not in literal_eval(pm_approve_users):
                raise UserError(_("You have no access to reject"))

        if self.is_gm_approve and not self.is_rfq_approve:
            gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_mashirah_oil_purchase.general_manager_ids', False)

            if self.env.user.id not in literal_eval(gm_approve_users):
                raise UserError(_("You have no access to reject"))

        self.activity_schedule('kg_mashirah_oil_purchase.reject_purchase_order_notification',
                               user_id=self.requested_by.id,
                               note=f' The user {self.env.user.name}  has rejected the approval of the Purchase Order {self.name}.')

        reject_purchase_order_notification_activity = self.env.ref(
            'kg_mashirah_oil_purchase.reject_purchase_order_notification')
        activity = self.activity_ids.filtered(
            lambda l: l.activity_type_id == reject_purchase_order_notification_activity)
        activity.action_done()

        purchase_manager_notification_activity = self.env.ref(
            'kg_mashirah_oil_purchase.purchase_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == purchase_manager_notification_activity)
        activity_1.unlink()

        general_manager_notification_activity = self.env.ref(
            'kg_mashirah_oil_purchase.general_manager_approval_notification')
        activity_2 = self.activity_ids.filtered(lambda l: l.activity_type_id == general_manager_notification_activity)
        activity_2.unlink()

        self.is_reject = True
        self.is_request = False
        self.is_pm_approve = False
        self.is_gm_approve = False
        self.is_rfq_approve = False

    def button_draft(self):
        res = super(KGPurchaseOrder, self).button_draft()
        self.is_reject = False
        self.is_request = True
        self.is_pm_approve = False
        self.is_gm_approve = False
        self.is_rfq_approve = False
        self.requested_by = False
        self.verified_by = False
        self.approved_by = False
        return res

    def kg_gm_approve(self):
        gm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.general_manager_ids', False)

        if self.env.user.id not in literal_eval(gm_approve_users):
            raise UserError(_("You have no access to approve"))

        else:
            gm_users = []
            general_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_purchase.general_manager_approval_notification')

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
                    self.activity_schedule('kg_mashirah_oil_purchase.purchase_order_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the GM approval of the Purchase Order {self.name}.')

            purchase_order_notification_activity = self.env.ref(
                'kg_mashirah_oil_purchase.purchase_order_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == purchase_order_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == purchase_order_notification_activity)
            activity_2.action_done()

            self.approved_by = self.env.user.id
            self.is_rfq_approve = True
            self.button_confirm()


    def button_confirm(self):
        for rec in self:
            if rec.is_reject:
                raise ValidationError(_("You cannot confirm because your request has been rejected"))

            if not rec.is_rfq_approve:
                raise ValidationError(_("You cannot do this action without approval"))

            if 'PO' not in rec.name:
                order_date = rec.date_order
                current_month_order_date = order_date.strftime('%m')
                current_year_order_date = order_date.strftime('%Y')
                # Search for existing purchase orders
                purchase = self.env['purchase.order'].search([('state','not in', ('done','purchase'))], order='id asc')
                # Filter purchase orders by the current month and year
                purchase_ids = purchase.filtered(
                    lambda x: x.date_order.month == order_date.month and x.date_order.year == order_date.year)
                if purchase_ids:
                    # Extract the last purchase order ID
                    last_po_id_str = purchase_ids[-1].name.split('/')[-1]
                    # Ensure the last_po_id_str is a valid integer
                    if last_po_id_str.isdigit():
                        next_value = int(last_po_id_str) + 1
                    else:
                        next_value = 1  # Default to 1 if the last ID is not a valid integer
                    # Update the record with the new PO number
                    rec.write({
                        'name': f'PO/{current_year_order_date}/{current_month_order_date}/{next_value:03d}'
                    })
                else:
                    # Initialize the PO number to 0001 for new records
                    rec.write({
                        'name': f'PO/{current_year_order_date}/{current_month_order_date}/001'
                    })
            return super(KGPurchaseOrder, self).button_confirm()



    def button_cancel(self):
        res = super(KGPurchaseOrder, self).button_cancel()
        self.is_request = False
        self.is_pm_approve = False
        self.is_gm_approve = False
        self.is_rfq_approve = False
        self.requested_by = False
        self.verified_by = False
        self.approved_by = False
        return res




class KGPurchaseorderline(models.Model):
    _inherit = 'purchase.order.line'

    @api.constrains('product_qty', 'qty_received')
    def check_product_qty_qty_received(self):
        for record in self:
            if record.product_qty < record.qty_received:
                raise UserError(_('The quantity received cannot exceed the product quantity.'))
