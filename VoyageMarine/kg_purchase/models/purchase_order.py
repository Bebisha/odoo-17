# -*- coding: utf-8 -*-

from datetime import date

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class KGPurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = 'Request For Quotation'

    po_type = fields.Selection([('local', 'Local'), ('meast', 'Middle east'), ('international', 'International'),
                                ('sisconcern', 'Sister Concern'), ('subcontracting', 'Subcontracting')],
                               default='sisconcern', string="Vendor Type", related='partner_id.po_type', store=True)
    requested_by = fields.Many2one("res.users", string="Requested By", copy=False)
    verified_by = fields.Many2one("res.users", string="Verified By", copy=False)
    approved_by = fields.Many2one("res.users", string="Approved by", copy=False)
    is_request = fields.Boolean(string="Is Request", default=False, copy=False)
    is_pm_approve = fields.Boolean(string="Is Purchase Manager Approve", default=False, copy=False)
    is_gm_approve = fields.Boolean(string="Is General Manager Approve", default=False, copy=False)
    is_rfq_approve = fields.Boolean(string="Is RFQ Approve", default=False, copy=False)
    is_reject = fields.Boolean(string="Is Reject", default=False, copy=False)
    po_note = fields.Html('Po Note',copy=False)
    rfq_note = fields.Html('RFQ Note')
    project_ids = fields.Many2many(
        'project.project',
        string='Project',
        help="Project related to this purchase order."
    )
    estimation_id = fields.Many2one("crm.estimation", string="Estimation")
    opportunity_id = fields.Many2one("crm.lead", string="Opportunity")
    terms_conditions_id = fields.Many2one('purchase.terms.conditions', string="Terms & Conditions")
    is_editable = fields.Boolean(string="Is Editable", default=True, copy=False)
    amount_in_currency = fields.Float(string="Amount In Currency (AED)", compute="compute_amount_in_currency")

    partner_id = fields.Many2one('res.partner', string='Vendor', required=False, change_default=True, tracking=True,
                                 check_company=True,
                                 help="You can find a vendor by its Name, TIN, Email or Internal Reference.")
    x_new_vendor_remark = fields.Char(string="Vendor Remark", copy=False)

    need_tm_approve = fields.Boolean(default=False, string="Need TM Approve", compute="compute_tm_approve")
    so_ids = fields.Many2many("sale.order", string="Sales Reference")
    scheduled_date = fields.Datetime(string="Scheduled Date", compute="compute_scheduled_date")
    subcategory_id = fields.Many2one("sub.category", string="Sub Category")
    freight_bill_ids = fields.Many2many("account.move", string="Freight Bill", compute="compute_freight_bill")

    company_currency_id = fields.Many2one("res.currency", string="Company Currency", related="company_id.currency_id")
    so_value = fields.Monetary(string="Sales Order Value", currency_field='company_currency_id',
                               compute="compute_so_value")
    shipping_documents_status = fields.Char(string="Shipping Document Status")

    overdue_days = fields.Char(string="Overdue Days", compute="compute_overdue_days")
    vessel_id = fields.Many2one('vessel.code', string='Vessel')
    rfq_id = fields.Many2one('purchase.order', string='RFQ Reference')
    rfq_ref = fields.Char( string='RFQ Reference')
    vendor_group_id = fields.Many2one('vendor.group', string="Vendor Group", related='partner_id.vendor_group_id')
    purchase_type_id = fields.Many2one("purchase.type", string="Purchase Type")
    purchase_division = fields.Char('Purchase Division', domain='purchase_type_id.purchase_division')
    purchase_division_id = fields.Many2one('purchase.division', string='Purchase Division', required=True, domain="[('purchase_type_id', '=', purchase_type_id)]")
    code = fields.Char('Purchase Code', related='purchase_type_id.code')
    purchase_acknowledgment = fields.Boolean('Purchase Acknowledgment')


    remarks = fields.Char(string="Remarks")

    payment_status = fields.Selection(
        [('not_paid', 'Not Paid'), ('in_payment', 'In Payment'), ('paid', 'Paid'), ('partial', 'Partially Paid'),
         ('reversed', 'Reversed'), ('invoicing_legacy', 'Invoicing App Legacy')], string="Payment Status",
        compute="_compute_payment_status")

    # def _prepare_invoice(self):
    #     """Prepare the dict of values to create the new invoice for a purchase order.
    #     """
    #     self.ensure_one()
    #     move_type = self._context.get('default_move_type', 'in_invoice')
    #
    #     partner_invoice = self.env['res.partner'].browse(self.partner_id.address_get(['invoice'])['invoice'])
    #     partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]
    #     done_pickings = self.picking_ids.filtered(lambda p: p.state == 'done')
    #     invoice_vals = {
    #         'ref': self.partner_ref or '',
    #         'move_type': move_type,
    #         'narration': self.notes,
    #         'currency_id': self.currency_id.id,
    #         'partner_id': partner_invoice.id,
    #         'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(partner_invoice)).id,
    #         'payment_reference': self.partner_ref or '',
    #         'partner_bank_id': partner_bank_id.id,
    #         'invoice_origin': self.name,
    #         'invoice_payment_term_id': self.payment_term_id.id,
    #         'invoice_line_ids': [],
    #         'company_id': self.company_id.id,
    #         'picking_ids': [(6, 0, done_pickings.ids)],
    #
    #     }
    #     print(invoice_vals,"invoice_valssssssssssssssss")
    #     return invoice_vals

    def get_sale(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', '=', self.so_ids.ids)],
            'context': {'create': False}
        }

    def _compute_payment_status(self):
        for rec in self:
            if rec.invoice_ids:
                statuses = rec.invoice_ids.mapped('payment_state')
                if 'not_paid' in statuses:
                    rec.payment_status = 'not_paid'
                elif 'partial' in statuses:
                    rec.payment_status = 'partial'
                elif 'in_payment' in statuses:
                    rec.payment_status = 'in_payment'
                elif all(status == 'paid' for status in statuses):
                    rec.payment_status = 'paid'
                else:
                    rec.payment_status = 'invoicing_legacy'
            else:
                rec.payment_status = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.vendor_group_id = self.partner_id.vendor_group_id
            self.po_type = self.partner_id.po_type
        else:
            self.vendor_group_id = False

    def action_preview_purchase_order(self):
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/kg_purchase.standard_pdf_purchase_quotation_report/%s' % self.id
        }

    def compute_overdue_days(self):
        for rec in self:
            overdue_data = []
            if rec.invoice_ids:
                for li in rec.invoice_ids:
                    if li.state == 'posted' and li.invoice_date_due and li.invoice_date_due < date.today() and li.payment_state in [
                        'not_paid', 'partial']:
                        overdue_days = (date.today() - li.invoice_date_due).days
                        overdue_data.append(f"{li.name} - {overdue_days} days")
            rec.overdue_days = "\n".join(overdue_data) if overdue_data else 0

    def compute_so_value(self):
        for rec in self:
            if rec.so_ids:
                rec.so_value = sum(rec.so_ids.mapped('amount_in_currency'))
            else:
                rec.so_value = 0.00

    def compute_freight_bill(self):
        for rec in self:
            move_id = self.env['account.move'].search(
                [('is_freight_bill', '=', True), ('invoice_origin', '=', rec.name)])
            if move_id:
                rec.freight_bill_ids = [(6, 0, move_id.ids)]
            else:
                rec.freight_bill_ids = False

    def open_freight_bills(self):
        return {
            'name': 'Freight Bills',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.freight_bill_ids.ids)],
            'target': 'current',
            'context': {'create': False}
        }

    def compute_scheduled_date(self):
        for rec in self:
            if rec.picking_ids:
                rec.scheduled_date = rec.picking_ids[0].scheduled_date
            else:
                rec.scheduled_date = False

    def compute_tm_approve(self):
        for rec in self:
            if rec.amount_in_currency:
                if rec.amount_in_currency >= 50000:
                    rec.need_tm_approve = True
                else:
                    rec.need_tm_approve = False
            else:
                rec.need_tm_approve = False

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('requested', 'Requested'),
        ('pm_approved', 'PM Approved'),
        ('gm_approved', 'Top Management Approved'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')])

    @api.model
    def _get_pm_approvers(self):
        params = self.env['ir.config_parameter'].sudo().get_param('kg_purchase.purchase_manager_ids', False)
        if params:
            qty_ids = eval(params)
            if isinstance(qty_ids, list):
                return qty_ids
            else:
                return []
        else:
            return []

    @api.model
    def _get_gm_approvers(self):
        params = self.env['ir.config_parameter'].sudo().get_param('kg_purchase.general_manager_ids', False)
        if params:
            qty_ids = eval(params)
            if isinstance(qty_ids, list):
                return qty_ids
            else:
                return []
        else:
            return []

    @api.model
    def _get_dep_approvers(self):
        params = self.env['ir.config_parameter'].sudo().get_param('kg_purchase.account_team_ids', False)
        if params:
            qty_ids = eval(params)
            if isinstance(qty_ids, list):
                return qty_ids
            else:
                return []
        else:
            return []

    gm_approver_id = fields.Many2many(
        'res.users',
        string='Top Manager', relation='gm_approver_id',
        domain=lambda self: [('id', 'in', self._get_gm_approvers())]
    )

    pm_approver_id = fields.Many2many(
        'res.users',
        string='PM Approver', relation='pm_approver_id',
        domain=lambda self: [('id', 'in', self._get_pm_approvers())]
    )
    dep_approver_id = fields.Many2many(
        'res.users', relation='dep_approver_id',
        string='Dep Approver',
        domain=lambda self: [('id', 'in', self._get_dep_approvers())]
    )

    @api.model
    def create(self, vals):
        if not vals.get('po_note'):
            print("llllllllllllllll")
            vals['po_note'] = """
                      <p>
                Please ensure all items are delivered in good condition and meet the specifications listed.
                If there are any issues or delays, contact us immediately at
                <a href="mailto:purchase@voyagemarine.ae">purchase@voyagemarine.ae</a>.
            </p>
                  """
        res = super().create(vals)

        if res.partner_id:
            res._set_vendor_sequence_name()

        return res


    def _set_vendor_sequence_name(self):
        """Reusable function to generate PO name based on vendor."""
        self.ensure_one()
        vendor = self.partner_id
        vendor_code = vendor.vendor_code or vendor.ref or vendor.name or ''

        if not vendor_code:
            self.name = _('New')
            return
        existing_rfqs = self.env['purchase.order'].search([
            ('partner_id', '=', vendor.id),
            ('name', 'ilike', f"{vendor_code}_")
        ])
        next_number = len(existing_rfqs) + 1
        next_number_str = str(next_number).zfill(2)
        new_name = f"{vendor_code}_{next_number_str}"
        self.name = new_name
        self.rfq_ref = new_name

    #
    #     partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
    #     vendor_code = partner_id.vendor_code
    #     print(res, "resssssssssssssss")
    #     sequence = self.env['ir.sequence'].next_by_code('rfq.seq')
    #
    #     if vals.get('opportunity_id'):
    #         est = vals['opportunity_id']
    #         est_name = self.env['crm.lead'].browse(est)
    #         estimation = est_name.enq_no or 'EST'
    #         res.name = f"{estimation}_{vendor_code}_{sequence}"
    #     # elif vals['estimation_id'] in vals.keys():
    #     #     partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
    #     #     sequence = self.env['ir.sequence'].next_by_code('rfq.seq')
    #     #     vendor_code = partner_id.vendor_code
    #     #     est = vals['estimation_id']
    #     #     est_name = self.env['crm.estimation'].browse(est)
    #     #     estimation = est_name.name
    #     #     res['name'] = f"{estimation}_{vendor_code}_{sequence}"
    #     else:
    #         sequence = self.env['ir.sequence'].next_by_code('rfq.seq.new')
    #         res.name = f"{vendor_code}_{sequence}"
    #
    #     return res

    def kg_request(self):
        """Send notification to PM Approvers."""
        if not self.order_line:
            raise ValidationError("Empty Order Lines: Add items to continue !!")

        if not self.purchase_type_id:
            raise ValidationError(_("Please select the purchase type !!"))

        pm_approver_ids = self.pm_approver_id.ids  # This is a list of IDs, not a recordset

        # Ensure that pm_approver_ids is not empty
        if not pm_approver_ids:
            raise ValidationError(_("Please select at least one PM Approver"))

        if not self.gm_approver_id and self.need_tm_approve:
            raise ValidationError(_("Please Select General Manager in Configuration"))

        # Convert pm_approver_ids to a recordset using browse
        pm_approver = self.env['res.users'].browse(pm_approver_ids)

        # Check if pm_approver is valid (not empty)
        if not pm_approver:
            raise ValidationError(_("Selected PM Approvers are invalid."))

        self.requested_by = self.env.user.id
        self.is_pm_approve = True
        self._action_schedule_activities_request(pm_approver)
        self.state = 'requested'

    def _action_schedule_activities_request(self, pm_approver):
        records = []

        for user in pm_approver:
            # Ensure user is a res.users record and has an id
            if user:
                record = self.activity_schedule(
                    'kg_purchase.purchase_manager_approval_notification',
                    user_id=user.id,
                    note=f'The User {self.env.user.name} requests the Purchase Manager to approve the Purchase Order {self.name}. Please verify and approve.'
                )
                records.append(record)
        return records

    def kg_pm_approve(self):
        """Approve Purchase Order for PM and request GM approval."""
        if not self.order_line:
            raise ValidationError("Empty Order Lines: Add items to continue !!")
        pm_approve_users = self.pm_approver_id.ids
        if self.env.user.id not in pm_approve_users:
            raise UserError(_("You have no access to approve"))
        self.verified_by = self.env.user.id
        self.is_gm_approve = True
        self.state = 'pm_approved'

        if not self.need_tm_approve:
            self.is_rfq_approve = True
            self.button_confirm()
        self._schedule_activities_pm_approve(pm_approve_users)

    def _schedule_activities_pm_approve(self, pm_approve_users):
        """Schedule activities for GM approval after PM approval."""

        purchase_manager_notification_activity = self.env.ref('kg_purchase.purchase_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == purchase_manager_notification_activity)
        not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)
        not_current_user_confirm.unlink()
        activity_2 = self.activity_ids.filtered(lambda l: l.activity_type_id == purchase_manager_notification_activity)
        activity_2.action_done()
        if self.need_tm_approve:
            for user in pm_approve_users:
                self.activity_schedule(
                    'kg_purchase.general_manager_approval_notification',
                    user_id=user,
                    note=f'The user {self.env.user.name} has approved the Purchase Manager approval and requests the GM to approve the Purchase Order {self.name}. Please verify and approve.'
                )

    def kg_reject(self):
        """Reject the Purchase Order, send rejection notification."""
        if not self.is_gm_approve:
            pm_approve_users = self.pm_approver_id.ids
            if self.env.user.id not in pm_approve_users:
                raise UserError(_("You have no access to reject"))

        if self.is_gm_approve and not self.is_rfq_approve:
            gm_approve_users = self.gm_approver_id.ids
            if self.env.user.id not in gm_approve_users:
                raise UserError(_("You have no access to reject"))
        self.is_reject = True
        self.is_request = False
        self.is_pm_approve = False
        self.is_gm_approve = False
        self.is_rfq_approve = False
        self._schedule_activities_reject()

    def _schedule_activities_reject(self):
        self.activity_schedule(
            'kg_purchase.reject_purchase_order_notification',
            user_id=self.create_uid.id,
            note=f'The user {self.env.user.name} has rejected the approval of the Purchase Order {self.name}.'
        )

        reject_purchase_order_notification_activity = self.env.ref('kg_purchase.reject_purchase_order_notification')
        activity = self.activity_ids.filtered(
            lambda l: l.activity_type_id == reject_purchase_order_notification_activity)
        activity.action_done()
        purchase_manager_notification_activity = self.env.ref('kg_purchase.purchase_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == purchase_manager_notification_activity)
        activity_1.unlink()
        general_manager_notification_activity = self.env.ref('kg_purchase.general_manager_approval_notification')
        activity_2 = self.activity_ids.filtered(lambda l: l.activity_type_id == general_manager_notification_activity)
        activity_2.unlink()

    def kg_gm_approve(self):
        if not self.order_line:
            raise ValidationError("Empty Order Lines: Add items to continue !!")
        gm_approve_users = self.gm_approver_id.ids
        if self.env.user.id not in gm_approve_users:
            raise UserError(_("You have no access to approve"))
        self.approved_by = self.env.user.id
        self.is_rfq_approve = True

        self.button_confirm()
        self._schedule_activities_gm_approve(gm_approve_users)
        self.state = 'gm_approved'

    def _schedule_activities_gm_approve(self, gm_approve_users):
        general_manager_notification_activity = self.env.ref('kg_purchase.general_manager_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == general_manager_notification_activity)
        not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

        not_current_user_confirm.unlink()
        activity_2 = self.activity_ids.filtered(lambda l: l.activity_type_id == general_manager_notification_activity)
        activity_2.action_done()

        for requested_by in gm_approve_users:
            self.activity_schedule(
                'kg_purchase.purchase_order_approval_notification',
                user_id=requested_by,
                note=f'The user {self.env.user.name} has approved the GM approval of the Purchase Order {self.name}.'
            )

        purchase_order_notification_activity = self.env.ref('kg_purchase.purchase_order_approval_notification')
        activity_1 = self.activity_ids.filtered(lambda l: l.activity_type_id == purchase_order_notification_activity)
        not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

        not_current_user_confirm.unlink()
        activity_2 = self.activity_ids.filtered(lambda l: l.activity_type_id == purchase_order_notification_activity)
        activity_2.action_done()

    def compute_amount_in_currency(self):
        for rec in self:
            if rec.amount_total and rec.currency_id and rec.date_order:
                if rec.currency_id != self.env.company.currency_id:
                    converted_amount = rec.currency_id._convert(
                        rec.amount_total, self.env.company.currency_id, self.env.company,
                        rec.date_order.date()
                    )
                    rec.amount_in_currency = converted_amount
                else:
                    rec.amount_in_currency = rec.amount_total
            else:
                rec.amount_in_currency = rec.amount_total

    @api.onchange('terms_conditions_id')
    def _onchange_terms_conditions_id(self):
        if self.terms_conditions_id:
            self.notes = self.terms_conditions_id.description
        else:
            self.notes = False

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

    is_picking_created = fields.Boolean(string="Picking Created", default=False)
    is_confirming = fields.Boolean(string="Is Confirming", default=False)

    def _create_picking(self):
        self.is_editable = True
        StockPicking = self.env['stock.picking']
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                order = order.with_company(order.company_id)
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))

                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    pickings = picking
                else:
                    picking = pickings[0]
                picking.write({'vessel_id': order.vessel_id.id})
                moves = order.order_line._create_stock_moves(picking)

                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()

                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                # Get following pickings (created by push rules) to confirm them as well.
                forward_pickings = self.env['stock.picking']._get_impacted_pickings(moves)
                (pickings | forward_pickings).action_confirm()
                order.is_picking_created = True
                picking.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': picking, 'origin': order},
                    subtype_xmlid='mail.mt_note',
                )
                order.is_editable = False
                # order.vessel_id.id = picking.vessel_id.id

        return True

    # def write(self, values):
    #     if not values.get('po_note'):
    #         print("llllllllllllllll")
    #         values['po_note'] = """
    #                               <p>
    #                         Please ensure all items are delivered in good condition and meet the specifications listed.
    #                         If there are any issues or delays, contact us immediately at
    #                         <a href="mailto:purchase@voyagemarine.ae">purchase@voyagemarine.ae</a>.
    #                     </p>
    #                           """
    #     return super(KGPurchaseOrder, self).write(values)

    def button_confirm(self):
        for order in self:
            order.name = self.env['ir.sequence'].next_by_code('purchase.seq')
            if not order.order_line:
                raise ValidationError("Empty Order Lines: Add items to continue !!")
            #
            # if order.order_line and any(not li.product_id and not li.display_type for li in order.order_line):
            #     raise ValidationError(_("Create Product for non inventory items !!"))
            if order.order_line and any(not li.product_uom for li in order.order_line):
                raise ValidationError(_("Select the product's Unit of Measure (UOM) !!"))
            if order.is_reject:
                raise ValidationError(_("You cannot confirm because your request has been rejected"))

            if not order.is_rfq_approve:
                raise ValidationError(_("You cannot do this action without approval"))
            if order.partner_id.state != 'approval':
                raise UserError('Vendor must be approved to confirm the purchase order.')

            order.is_confirming = True
            if order.pr_requisition_id :
                pr = order.pr_requisition_id
                print(pr,"prprprprpr")
                if pr:
                    pr.last_po_confirm_date = fields.Date.today()
                else :
                    pr.last_po_confirm_date = False

            # if order.state not in ['draft', 'sent', 'gm_approved']:
            #     continue
            order.order_line._validate_analytic_distribution()
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])

            if order.picking_ids:
                for picking in order.picking_ids:
                    if not picking.expected_arrival_date:
                        picking.expected_arrival_date = order.date_planned

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

    @api.constrains('estimation_id', 'amount_total', 'order_line', 'currency_id')
    def check_purchase_estimate_material_cost(self):
        for rec in self:
            if rec.date_order:
                convert_date = rec.date_order.date()
            else:
                convert_date = date.today()

            if rec.estimation_id and rec.estimation_id.material_cost:
                if rec.estimation_id.currency_id.id == rec.currency_id.id:
                    if rec.amount_total > rec.estimation_id.material_cost:
                        raise ValidationError(
                            "Purchase Cost cannot be greater than than Estimate Material Cost.\n\t Material Cost is %.2f %s" % (
                                rec.estimation_id.material_cost, rec.currency_id.name))
                else:
                    converted_amount = rec.currency_id._convert(
                        rec.amount_total, rec.estimation_id.currency_id, self.env.company,
                        convert_date
                    )

                    if converted_amount and converted_amount > rec.estimation_id.total_material_currency:
                        raise ValidationError(
                            "Purchase Cost cannot be greater than than Estimate Material Cost.\n\t Material Cost is %.2f %s" % (
                                rec.estimation_id.total_material_currency, rec.estimation_id.currency_id.name))

    def create_freight_bill(self):
        vals = {
            'invoice_origin': self.name,
            'move_type': 'in_invoice',
            'is_freight_bill': True
        }
        self.env['account.move'].create(vals)
