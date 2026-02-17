import ast
import base64
from datetime import datetime

from odoo.tools import formatLang, float_is_zero
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, _, api
import werkzeug
import re
from ast import literal_eval


class KGSaleOrderInherit(models.Model):
    _inherit = "sale.order"
    _description = 'Quotation'

    type_id = fields.Selection([('local', 'Local'), ('meast', 'Middle east'), ('international', 'International'),
                                ('sisconcern', 'Sister Concern'), ('subcontracting', 'Subcontracting')],
                               default='sisconcern', string="Type",related='partner_id.po_type', store=True)

    qtn_requested = fields.Boolean(default=False, string="Quotation Requested", copy=False)
    qtn_approved = fields.Boolean(default=False, string="Quotation Approved", copy=False)
    qtn_requested_approved = fields.Boolean(default=False, string="Quotation Requested Approved", copy=False)
    sale_revision_reason = fields.Char(string="Revision Reason", copy=False)
    customer_reference = fields.Char(string="Customer Reference", copy=False)
    purchase_reference = fields.Char(string="Purchase Reference", copy=False)
    purchase_date = fields.Date(string="PO Date", copy=False)
    revision_count = fields.Integer(string="Revision Count", copy=False)
    revision_ids = fields.Many2many("sale.order", 'sale_revision_rel', 'kg_sale_rev_rel', string="Revisions",
                                    copy=False)
    main_revision_id = fields.Many2one("sale.order", string="Main Revision", copy=False)
    hide_revision_button = fields.Boolean(default=False, string="Hide Revision Button",
                                          compute="compute_hide_revision_button")

    qtn_so_line_ids = fields.One2many('sale.qtn.line', 'qtn_so_id', string="Quotation Line", copy=False)
    estimation_id = fields.Many2one("crm.estimation", string="Estimation", copy=False)
    po_attach_files = fields.Many2many('ir.attachment', string="Purchase Files")

    survey_id = fields.Many2one("survey.survey", string="Cancellation Feedback Survey", copy=False)
    survey_start_url = fields.Char('Survey URL', compute='_compute_survey_start_url', copy=False)
    order_type = fields.Selection(
        [('project', 'Project'), ('service', 'Service'), ('trade', 'Trading')], string='Order Type', default="service")

    advance_preview = fields.Html(compute="_compute_advance_preview", copy=False)
    amount_in_currency = fields.Float(string="Amount in Currency(AED)", compute="convert_amount_in_currency")

    is_approval_required = fields.Boolean(default=False, string='Approval Required', copy=False)
    is_hod_reject = fields.Boolean(default=False, string='IS HOD Rejected', copy=False)
    hod_approved = fields.Boolean(default=False, string='HOD Approved', copy=False)
    supervisor_approved = fields.Boolean(default=False, string='Supervisor Approved', copy=False)
    is_reject = fields.Boolean(string="Is Reject", default=False, copy=False)
    show_reject_button = fields.Boolean(string="Show Reject Button", default=False, copy=False)
    hide_reject_button = fields.Boolean(string="Hide Reject Button", default=False, copy=False)

    is_readonly = fields.Boolean(default=False, string="Readonly", compute="compute_is_readonly")

    partner_bank_id = fields.Many2one("res.partner.bank", string="Recipient Bank")
    vessel_name = fields.Char(string="Vessel")
    attention = fields.Many2one("res.partner", string='Attn')
    attn = fields.Char(string="Enquiry Attn")

    qtn_approved_user = fields.Many2one("res.users", string="Quotation", copy=False)
    hod_approved_user = fields.Many2one("res.users", string="Head of Department", copy=False)
    supervisor_approved_user = fields.Many2one("res.users", string="Management", copy=False)

    boe_ids = fields.Many2many("mrp.bom", string="BOE", copy=False)
    boe_count = fields.Integer(string="BOE Count", compute="compute_boe_count")
    bom_count = fields.Integer(string="BOE Count", compute="compute_bom_count")
    mo_count = fields.Integer(string="BOE Count", compute="compute_mo_count")
    boe_created = fields.Boolean(default=False, string="BOE Created", copy=False)
    is_display_vat_column = fields.Boolean(default=True, string="Is Display Vat Column", copy=False)
    need_boe = fields.Boolean(default=False, string="Need BOE", copy=False, compute="compute_need_boe")

    verify_payment_term = fields.Many2many("account.payment.term", string="New payment term", copy=False,
                                           compute="_compute_verify_payment_term", readonly=False)
    estimate_partner_ids = fields.Many2many("res.partner", string="Estimate Partners")
    package_id = fields.Many2one('package.list', string="Packing List")

    processing_doc_ids = fields.Many2many("processing.documents", string="Required Documents", copy=False,
                                        default=lambda self: self._default_processing_docs())

    checklist_line_ids = fields.One2many("checklist.lines", "so_id", string="Checklist Names")

    def get_file_name_from_folder(self):
        folder = self.env.ref('kg_voyage_marine_crm.document_inspection_form_folder')
        if not folder:
            return ''
        doc = self.env['documents.document'].search([('folder_id', '=', folder.id)], limit=1)
        return doc.name

    def _default_processing_docs(self):
        return self.env['processing.documents'].search([('is_default', '=', True)]).ids

    INVOICE_STATUS = [
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('partial', 'Partially Invoiced'),  # New status
        ('no', 'Nothing to Invoice'),
    ]

    invoice_status = fields.Selection(
        selection=INVOICE_STATUS,
        string="Invoice Status",
        compute='_compute_invoice_status',
        store=True
    )
    is_product_select = fields.Boolean(string="Select",
                                       help="To Select products from order line",
                                       copy=False, default=True)
    terms_conditions_id = fields.Many2one('sale.terms.conditions', string="Terms & Conditions")
    department_id = fields.Many2one('hr.department', string='Department', readonly=True)
    delivery_duration = fields.Char(string="Delivery Duration")
    vessel_id = fields.Many2one('vessel.code', string='Vessel')

    po_attachment = fields.Binary(string="PO Attachment")
    po_attachment_name = fields.Char(string="PO Filename")

    do_attachment = fields.Binary(string="DO / Airway Bill / Delivery Note")
    do_attachment_name = fields.Char(string="DO Filename")

    job_completion_attachment = fields.Binary(string="Job Completion Report (Service Report / DO / Timesheet)")
    job_completion_attachment_name = fields.Char(string="Job Completion Filename")

    SALE_ORDER_STATE = [
        ('draft', "Quotation"),
        ('pending', "Pending"),
        ('approved', "Approved"),
        ('sent', "Quotation Sent"),
        ('sale', "Sales Order"),
        ('rejected', "Rejected"),
        ('cancel', "Cancelled"),
    ]

    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')

    rejected_reason = fields.Char(string="Rejected Reason")
    division_id = fields.Many2one("kg.divisions", string="Division", tracking=True)
    quotation_reference = fields.Char(string="Quotation Number", copy=False)
    so_reference = fields.Char(string="Sale Order Number", copy=False)
    # is_rental_product = fields.Boolean(string="IS Rental Product" ,default=False,copy=False)
    #
    # @api.onchange('is_rental_order')
    # def _onchange_is_rental_order(self):
    #     """When toggling the order's rental flag, update all existing lines."""
    #     for order in self:
    #         for line in order.order_line:
    #             line.is_rental_product = order.is_rental_product

    packing_form_count = fields.Integer(
        string="Packing Count",
        compute="_compute_form_counts_packing"
    )
    proforma_invoice_no = fields.Char(string="Proforma Invoice No", copy=False, default=False)
    approval_status = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected','Rejected'),
        ('none', 'No Request')
    ], compute='_compute_approval_statuss', store=True)
    company_partner_id = fields.Many2one('res.partner', related='company_id.partner_id', string='Account Holder', readonly=True, store=False)

    bank_id = fields.Many2many(
        'res.partner.bank',
        string="Bank Account"

    )
    available_reserved_lots = fields.Boolean()


    @api.depends('qtn_requested', 'qtn_approved','is_reject','state')
    def _compute_approval_statuss(self):
        for record in self:
            if record.qtn_approved:
                record.approval_status = 'approved'
            elif record.is_reject and not record.qtn_approved and record.qtn_requested:
                record.approval_status = 'rejected'
            elif record.qtn_requested:
                record.approval_status = 'pending'
            else:
                record.approval_status = 'none'

    def open_rfq_wizard(self):
        return {
            'name': 'Create RFQ',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'rfq.wizard',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
            }
        }

    def _get_discount_product(self):
        """Return product.product used for discount line"""
        self.ensure_one()
        discount_product = self.company_id.sale_discount_product_id
        if not discount_product:
            if (
                self.env['product.product'].check_access_rights('create', raise_exception=False)
                and self.company_id.check_access_rights('write', raise_exception=False)
                and self.company_id._filter_access_rules_python('write')
                and self.company_id.check_field_access_rights('write', ['sale_discount_product_id'])
            ):
                self.company_id.sale_discount_product_id = self.env['product.product'].create(
                    self._prepare_discount_product_values()
                )
            else:
                raise ValidationError(_(
                    "There does not seem to be any discount product configured for this company yet."
                    " You can either use a per-line discount, or ask an administrator to grant the"
                    " discount the first time."
                ))
            discount_product = self.company_id.sale_discount_product_id
        return discount_product

    def _compute_form_counts_packing(self):
        for order in self:
            package_list = self.env['package.list'].search_count([('sale_order_id', '=', self.id)])
            order.packing_form_count = package_list

    def action_packing(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Packing List',
            'view_mode': 'tree,form',
            'res_model': 'package.list',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'create': False}
        }



    def action_open_package_list(self):
        package_list = self.env['package.list'].search([('sale_order_id', '=', self.id)])
        selected_lines = self.order_line.filtered('is_product_select')
        if not selected_lines:
            raise UserError("You must select at least one product before creating a package list.")
        if package_list:
            raise UserError("Already created this recoder")
        if not package_list:
            packing_lines = []
            for line in selected_lines:
                line_data = {
                    'product_id': line.product_id.id,
                    'product_tempt_id': line.product_template_id.id,
                    'description': line.name,
                    'quantity': line.product_uom_qty,
                    'unit_price': line.price_unit,
                    'product_uom_id': line.product_uom.id,
                    'subtotal': line.price_subtotal,
                }
                packing_lines.append((0, 0, line_data))
            package_list = self.env['package.list'].create({
                'sale_order_id': self.id,
                'vessel_id': self.vessel_id.id,
                'job_no': self.job_sheet_no,
                'po_ids':self.po_ids.ids,
                'po_reference':self.purchase_reference,
                # 'partner_id': self.partner_id.id,
                'packing_line_ids': packing_lines,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Package List',
            'res_model': 'package.list',
            'view_mode': 'form',
            'res_id': package_list.id,
            'target': 'current',
        }

    @api.model
    def get_qtn_approvers(self):
        params = self.env['ir.config_parameter'].sudo().get_param('quotation_approve_ids', False)
        if params:
            qty_ids = eval(params)
            if isinstance(qty_ids, list):
                return qty_ids
            else:
                return []
        else:
            return []

    @api.model
    def get_hod_approvers(self):
        params = self.env['ir.config_parameter'].sudo().get_param('hod_approve_ids', False)
        if params:
            qty_ids = eval(params)
            if isinstance(qty_ids, list):
                return qty_ids
            else:
                return []
        else:
            return []

    @api.model
    def get_sup_approvers(self):
        params = self.env['ir.config_parameter'].sudo().get_param('supervisor_ids', False)
        if params:
            qty_ids = eval(params)
            if isinstance(qty_ids, list):
                return qty_ids
            else:
                return []
        else:
            return []

    qtn_approve_user_ids = fields.Many2many("res.users", string="QTN Approve Users",
                                            domain=lambda self: [('id', 'in', self.get_qtn_approvers())], required=True)
    hod_approve_user_ids = fields.Many2many("res.users", string="Head of Department Approve Users",
                                            relation="hod_approve_user_ids",
                                            domain=lambda self: [('id', 'in', self.get_hod_approvers())]
                                            )
    sup_approve_user_ids = fields.Many2many("res.users", string="Management Approve Users",
                                            relation="sup_approve_user_ids",
                                            domain=lambda self: [('id', 'in', self.get_sup_approvers())]
                                            )

    qtn_approver_id = fields.Many2one("res.users", string="Quotation Approver",
                                      domain="[('id', 'in', qtn_approve_user_ids)]")

    freight_custom = fields.Monetary(string="Freight", currency_field="currency_id",
                                     help="Freight charges for this order.")
    custom_charge = fields.Monetary(string="Custom", currency_field="currency_id",
                                    help="Customs charges for this order.")

    purchase_status = fields.Selection(
        [('ac_acknowledged', 'MR Acknowledged'), ('in_stock', 'In Stock'), ('rfq', 'RFQ'),
         ('po_raised', 'PO Raised'), ('received', 'Received'), ('partial_stock', 'Partial Stock'),
         ('partial_po', 'Partial PO')],
        string="Purchase Status",
        compute="compute_purchase_status")
    so_confirmed = fields.Boolean(default=False, string="SO Confirmed", copy=False)

    requested_revision = fields.Boolean(default=False, string="Requested Revision", copy=False)
    approved_revision = fields.Boolean(default=False, string="Approved Revision", copy=False)
    created_revision = fields.Boolean(default=False, string="Created Revision", copy=False)

    po_ids = fields.Many2many("purchase.order", string="Purchase Ref", copy=False, compute="compute_po_ids")
    rfq_ids = fields.Many2many("purchase.order",'rfq_po_id_rel', string="Rfq Ref", copy=False,)
    so_po_ids = fields.Many2many("purchase.order", 'so_po_ids_rel', string="Sales PO Ref",copy=False)
    mr_po_ids = fields.Many2many("purchase.order", 'mr_po_ids_rel', string="MR PO Ref", compute="compute_mr_po_ids",copy=False)
    est_po_ids = fields.Many2many("purchase.order", 'est_po_ids_rel', string="Estimation PO Ref",copy=False,
                                  compute="compute_est_po_ids")
    enq_po_ids = fields.Many2many("purchase.order", 'enq_po_ids_rel', string="Enquiry PO Ref",copy=False,
                                  compute="compute_enq_po_ids")

    mr_created = fields.Boolean(default=False, copy=False, string="MR Created")
    mr_ids = fields.Many2many("material.purchase.requisition", string="Material Requisition",
                              compute="compute_mr_records")
    mr_count = fields.Integer(string="MR Count", compute="compute_mr_count")
    need_mr = fields.Boolean(default=False, copy=False, compute="compute_need_mr")

    delivery_terms_id = fields.Many2one("delivery.terms", string="Delivery Terms",default= lambda self: self.env['delivery.terms'].search([('name', '=', 'As scheduled above')], limit=1))
    delivery_terms_condition = fields.Html(string='Terms & Conditions')

    without_revision_qtn = fields.Char(string="W/O Revision QTN", copy=False)
    revision_id = fields.Many2one("sale.order", string="Revision Number", tracking=True, readonly=True)

    payment_status = fields.Selection(
        [('not_paid', 'Not Paid'), ('in_payment', 'In Payment'), ('paid', 'Paid'), ('partial', 'Partially Paid'),
         ('reversed', 'Reversed'), ('invoicing_legacy', 'Invoicing App Legacy')], string="Payment Status",
        compute="_compute_payment_status")

    jr_no = fields.Char('JR.No', copy=False, readonly=True, related="opportunity_id.jr_no")

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

    def compute_est_po_ids(self):
        for rec in self:
            if rec.estimation_id and rec.estimation_id.po_ids:
                rec.est_po_ids |= rec.estimation_id.po_ids
            else:
                rec.est_po_ids = False

    def compute_enq_po_ids(self):
        for rec in self:
            print()
            if rec.opportunity_id:
                rec.enq_po_ids |= rec.opportunity_id.po_ids | rec.opportunity_id.rfq_ids
            else:
                rec.enq_po_ids = False

    def compute_mr_po_ids(self):
        for rec in self:
            pur_ids = self.env['purchase.requisitions'].search([('so_id', '=', rec.id)])
            if pur_ids and pur_ids.purchase_order_ids:
                rec.mr_po_ids = pur_ids.mapped('purchase_order_ids')
            else:
                rec.mr_po_ids = False

    def compute_po_ids(self):
        for rec in self:
            rec.po_ids = rec.est_po_ids | rec.enq_po_ids | rec.mr_po_ids | rec.so_po_ids

    # @api.onchange('order_line.sub_item_price')
    # def _onchange_update_unit_price_from_subitems(self):
    #     for line in self:
    #         print("jjjjjjjjjjjjjjjjjjjjj")
    #         # ✅ Only MAIN LINE
    #         if line.is_subitems:
    #             continue
    #
    #         sub_lines = line.order_id.order_line.filtered(
    #             lambda l: l.is_subitems
    #         )
    #
    #         sub_total = sum(sub_lines.mapped('price_subtotal'))
    #
    #         if line.product_uom_qty:
    #             line.price_unit = line.base_price_unit + (sub_total / line.product_uom_qty)
    #         else:
    #             line.price_unit = line.base_price_unit



    @api.depends(
        'order_line.price_subtotal',
        'order_line.price_tax',
        'order_line.price_total',
        'freight_custom',
        'custom_charge',
        'order_line.sub_item_price'
    )
    def _compute_amounts(self):
        for order in self:
            # STEP 1: Update price_unit of main lines
            for line in order.order_line.filtered(lambda l: not l.display_type):
                if not line.main_line_id:
                    sub_lines = order.order_line.filtered(
                        lambda x: x.main_line_id.id == line.id
                    )

                    sub_total = sum(sub_lines.mapped('sub_item_price'))
                    line.sub_item_price = sub_total
                    if line.base_price_unit:
                        if sub_total:
                            line.price_unit = line.base_price_unit + sub_total
                    else:
                        if sub_total:
                            line.price_unit = line.price_unit + sub_total

            # STEP 2: Standard Odoo amount computation
            order = order.with_company(order.company_id)
            order_lines = order.order_line.filtered(lambda x: not x.display_type)

            if order.company_id.tax_calculation_rounding_method == 'round_globally':
                tax_results = order.env['account.tax']._compute_taxes([
                    line._convert_to_tax_base_line_dict()
                    for line in order_lines
                ])
                totals = tax_results['totals']
                amount_untaxed = totals.get(order.currency_id, {}).get('amount_untaxed', 0.0)
                amount_tax = totals.get(order.currency_id, {}).get('amount_tax', 0.0)
            else:
                amount_untaxed = sum(order_lines.mapped('price_subtotal'))
                amount_tax = sum(order_lines.mapped('price_tax'))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = (
                    order.amount_untaxed
                    + order.amount_tax
                    + order.freight_custom
                    + order.custom_charge
            )

    def compute_need_mr(self):
        for rec in self:
            if rec.order_line and any(li.product_id.detailed_type == 'product' for li in
                                      rec.order_line) and rec.qtn_approved and not rec.is_approval_required:
                rec.need_mr = True
            else:
                rec.need_mr = False

    def compute_mr_count(self):
        for rec in self:
            if rec.mr_ids:
                rec.mr_count = len(rec.mr_ids)
            else:
                rec.mr_count = 0

    def compute_mr_records(self):
        for rec in self:
            mr_id = self.env['material.purchase.requisition'].search([('so_id', '=', rec.id)])
            if mr_id:
                rec.mr_ids |= mr_id
            else:
                rec.mr_ids = False

    def action_create_mr(self):
        orderline = []
        add_lines = self.order_line.filtered(lambda m: m.product_id.detailed_type == 'product')
        if add_lines:
            # mr_ids = self.env['material.purchase.requisition'].search(
            #     [('so_id', '=', self.id), ('state', 'not in', ['reject', 'cancel'])])
            # if mr_ids:
            #
            # else:
            loc = self.warehouse_id.lot_stock_id.id
            for line in add_lines:
                line_vals = (0, 0, {
                    'code': line.code,
                    'product_id': line.product_id.id,
                    'description': line.name,
                    'qty': line.product_uom_qty,
                    'uom_id': line.product_uom.id,
                })
                orderline.append(line_vals)

            emp = self.env['hr.employee'].search([('name', '=', self.user_id.partner_id.name)])
            if len(emp) == 0:
                raise ValidationError("There is no employee linked with this user:" + self.user_id.partner_id.name)
            elif not emp.department_id:
                raise ValidationError("Add department for :" + self.user_id.partner_id.name)

            vals = {
                'employee_id': emp.id,
                'department_id': emp.department_id.id,
                'department_res_id': emp.department_id.id,
                'requisition_line_ids': orderline,
                'issue_against': 'location',
                'issue_location': loc,
                'so_id': self.id,
                'shipping_address_id': self.partner_shipping_id.id,
                'division_id': self.division_id.id,
                'vessel_id': self.vessel_id.id,
                'so_date': self.date_order.date(),
                'estimation_id': self.estimation_id.id,
                'lead_id': self.opportunity_id.id if self.opportunity_id else self.estimation_id.lead_id.id ,
            }
            self.env['material.purchase.requisition'].create(vals)
            self.mr_created = True
        else:
            raise ValidationError(
                "Material Requisition can only be created for storable products, but this Sale Order contains non-storable products.")

    user_approver = fields.Boolean(compute='_compute_is_approver', default=False)

    @api.depends('qtn_approve_user_ids', 'state')
    def _compute_is_approver(self):
        current_user = self.env.user
        self.user_approver = False
        for record in self:
            record.user_approver = (
                    current_user in record.qtn_approve_user_ids
            )

    material_request_date = fields.Date(
        string="Material Request Date",
        compute="compute_material_request_date"
    )

    def compute_material_request_date(self):
        for rec in self:
            dates = []
            for mr in rec.mr_ids:
                if mr.requisition_date:
                    dates.append(mr.requisition_date)
            if dates:
                rec.material_request_date = min(dates)
            else:
                rec.material_request_date = False

    invoice_state = fields.Selection(
        [('invoiced', 'Invoiced'),
         ('invoicing_pending', 'Invoicing Pending'),
         ('cancel', 'Cancelled'), ],
        string="Invoice Status",
        compute="compute_invoice_status"
    )

    def compute_invoice_status(self):
        for rec in self:
            if rec.invoice_ids:
                if all(invoice.state == 'draft' for invoice in rec.invoice_ids):
                    rec.invoice_state = 'invoiced'
                elif any(invoice.state == 'posted' for invoice in rec.invoice_ids):
                    rec.invoice_state = 'invoicing_pending'
                elif any(invoice.state == 'cancel' for invoice in rec.invoice_ids):
                    rec.invoice_state = 'cancel'
                else:
                    rec.invoice_state = False
            else:
                rec.invoice_state = False

    delivery_status = fields.Selection(
        selection_add=[
            ('picking_packing', 'Picking & Packing'),
            ('processing_shipping_documents', 'Processing Shipping Documents'),
            ('airway_bill_pending', 'Airway Bill Pending'),
            ('delivery_hold', 'Delivery Hold'),
            ('ready_for_pickup', 'Ready for Pickup'),
        ],
        compute='_compute_delivery_status',
        store=True,
    )

    @api.depends('picking_ids', 'picking_ids.state', 'state')
    def _compute_delivery_status(self):
        """Return ONLY valid/known keys, including the ones we added with selection_add."""
        for order in self:
            pickings = order.picking_ids
            if not pickings:
                order.delivery_status = 'pending'  # Odoo's original key for "Nothing to deliver"
                continue

            states = set(pickings.mapped('state'))

            if states == {'cancel'}:
                order.delivery_status = 'delivery_hold'
            elif states == {'done'}:
                order.delivery_status = 'full'  # keep Odoo's key for fully delivered
            elif 'done' in states:
                order.delivery_status = 'partial'
            elif 'assigned' in states:
                order.delivery_status = 'ready_for_pickup'
            elif states.issubset({'confirmed', 'waiting'}) or 'confirmed' in states or 'waiting' in states:
                order.delivery_status = 'processing_shipping_documents'
            elif 'draft' in states:
                order.delivery_status = 'picking_packing'
            else:
                order.delivery_status = 'started'  # Odoo's “to deliver”


    purchase_order_status = fields.Selection(
        [('under_approval', 'Under Approval'),
         ('forward_delivery', 'Forward Delivery'),
         ('ready_for_collection', 'Ready for Collection'),
         ('on_hold', 'On Hold'),
         ('in_transit', 'In Transit'),
         ('under_customs_clearance', 'Under Customs Clearance'),
         ('partially_received', 'Partially Received'),
         ('completely_received', 'Completely Received')],
        string="Purchase Order Status",
        compute="compute_purchase_order_status"
    )

    def compute_purchase_order_status(self):
        for rec in self:
            if rec.po_ids:
                if all(li.state in ['draft', 'sent'] for li in rec.po_ids):
                    rec.purchase_order_status = 'under_approval'
                elif all(
                        li.state in ['done', 'purchase'] and any(
                            picking.state == 'draft' for picking in li.picking_ids)
                        for li in rec.po_ids
                ):
                    rec.purchase_order_status = 'forward_delivery'
                elif all(
                        li.state in ['done', 'purchase'] and any(
                            picking.state == 'assigned' for picking in li.picking_ids)
                        for li in rec.po_ids
                ):
                    rec.purchase_order_status = 'ready_for_collection'
                elif any(li.state == 'cancel' for li in rec.po_ids):
                    rec.purchase_order_status = 'on_hold'
                elif all(li.state in ['done', 'purchase'] and li.receipt_status == 'in_transit' for li in rec.po_ids):
                    rec.purchase_order_status = 'in_transit'  # Order is in transit
                elif any(
                        li.state in ['done', 'purchase'] and li.receipt_status == 'under_customs' for li in rec.po_ids):
                    rec.purchase_order_status = 'under_customs_clearance'  # Under customs clearance
                elif all(
                        li.state in ['done', 'purchase'] and any(
                            picking.state == 'waiting' for picking in li.picking_ids)
                        for li in rec.po_ids
                ):
                    rec.purchase_order_status = 'partially_received'
                elif all(
                        li.state in ['done', 'purchase'] and any(
                            picking.state == 'done' for picking in li.picking_ids)
                        for li in rec.po_ids
                ):
                    rec.purchase_order_status = 'completely_received'  # All items received
                else:
                    rec.purchase_order_status = False
            else:
                rec.purchase_order_status = False

    def compute_purchase_status(self):
        for rec in self:
            pur_req_ids = self.env['purchase.requisitions'].search([('so_id', '=', rec.id)])
            if rec.po_ids:
                if pur_req_ids and any(pur.partial_po for pur in pur_req_ids):
                    rec.purchase_status = 'partial_po'
                elif any(li.state in ['draft', 'sent'] for li in rec.po_ids):
                    rec.purchase_status = 'rfq'
                elif any(li.state in ['done', 'purchase'] and li.receipt_status == 'pending' for li in rec.po_ids):
                    rec.purchase_status = 'po_raised'
                elif any(li.state in ['done', 'purchase'] and li.receipt_status == 'partial' for li in rec.po_ids):
                    rec.purchase_status = 'partial_stock'
                elif all(li.receipt_status == 'full' for li in rec.po_ids):
                    rec.purchase_status = 'received'
                else:
                    rec.purchase_status = False
            else:
                mr_id = self.env['material.purchase.requisition'].search([('so_id', '=', rec.id)], limit=1)
                if mr_id:
                    rec.purchase_status = 'ac_acknowledged'
                elif any(
                        li.product_id and li.product_id.qty_available >= li.product_uom_qty and li.product_id.detailed_type == 'product'
                        for li in rec.order_line):
                    rec.purchase_status = 'in_stock'
                elif pur_req_ids and any(pur.partial_po for pur in pur_req_ids):
                    rec.purchase_status = 'partial_po'
                else:
                    rec.purchase_status = False

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
            if employee:
                self.department_id = employee.department_id
            else:
                self.department_id = False

    @api.onchange('processing_doc_ids')
    def _onchange_processing_documents(self):
        if not self.processing_doc_ids:
            self.checklist_line_ids = [(5, 0, 0)]
            return

        selected_ids = list(set(self.processing_doc_ids.ids))  # remove duplicates
        existing_ids = self.checklist_line_ids.mapped('processing_document_id').ids

        commands = []

        # Remove unselected
        for line in self.checklist_line_ids:
            if line.processing_document_id.id not in selected_ids:
                commands.append((2, line.id))

        # Add newly selected
        for doc_id in selected_ids:
            if doc_id not in existing_ids:
                commands.append((0, 0, {
                    'processing_document_id': doc_id,
                    'checkbox': False,
                }))

        if commands:
            self.update({'checklist_line_ids': commands})

    @api.model
    def create(self, vals):
        if 'user_id' in vals and not vals.get('department_id'):
            user = self.env['res.users'].browse(vals['user_id'])
            employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
            if employee and employee.department_id:
                vals['department_id'] = employee.department_id.id

        division_id = self.env['kg.divisions'].search([('id', '=', vals.get('division_id'))], limit=1)

        if not vals.get('main_revision_id') and division_id:
            if vals.get('date_order'):
                order_date = vals.get('date_order')
                qtn_date = datetime.strptime(order_date, '%Y-%m-%d %H:%M:%S')
            else:
                qtn_date = datetime.now()

            year = qtn_date.strftime('%y')
            month = qtn_date.strftime('%m')

            sequence_number = division_id.qtn_sequence_id.next_by_id()
            update_seq = {
                'name': f"{division_id.division[0]}{year}{month}{sequence_number}"
            }
            vals.update(update_seq)
            vals['without_revision_qtn'] = vals['name']
        res = super(KGSaleOrderInherit, self).create(vals)
        if res.processing_doc_ids and not res.checklist_line_ids:
            res.checklist_line_ids = [
                (0, 0, {
                    'processing_document_id': doc.id,
                    'checkbox': False
                }) for doc in res.processing_doc_ids
            ]

        return res

    def _set_department_from_user(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)], limit=1)
        self.department_id = employee.department_id if employee else False

    @api.onchange('terms_conditions_id')
    def _onchange_terms_conditions_id(self):
        if self.terms_conditions_id:
            self.note = self.terms_conditions_id.description
        else:
            self.note = False

    @api.onchange('delivery_terms_id')
    def _onchange_delivery_terms_id(self):
        if self.delivery_terms_id:
            self.delivery_terms_condition = self.delivery_terms_id.description
        else:
            self.delivery_terms_condition = False

    def _get_invoiceable_lines(self, final=False):
        """Return the invoiceable lines for order `self`."""
        down_payment_line_ids = []
        invoiceable_line_ids = []
        pending_section = None
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        sol_id = self.order_line.filtered(lambda line_select: (
                                                                      line_select.is_inv_select or line_select.is_downpayment) or
                                                              True not in self.order_line.mapped(
            'is_inv_select') or line_select.display_type == 'line_section' or line_select.display_type == 'line_note')

        if sol_id:
            for line in sol_id:
                if line.display_type == 'line_section':
                    # Only invoice the section if one of its lines is invoiceable
                    pending_section = line
                    continue
                if line.display_type != 'line_note' and float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if line.qty_to_invoice > 0 or (line.qty_to_invoice < 0 and final) or line.display_type == 'line_note':
                    if line.is_downpayment:
                        # Keep down payment lines separately, to put them together
                        # at the end of the invoice, in a specific dedicated section.
                        down_payment_line_ids.append(line.id)
                        continue
                    if pending_section:
                        invoiceable_line_ids.append(pending_section.id)
                        pending_section = None
                    invoiceable_line_ids.append(line.id)

            return self.env['sale.order.line'].browse(invoiceable_line_ids + down_payment_line_ids)
        else:
            raise UserError(_('There is no invoiceable line. Please make sure '
                              'that a order line is selected'))

    def _prepare_invoice(self):
        invoice_vals = super(KGSaleOrderInherit, self)._prepare_invoice()
        attachment_ids = []
        InvoiceAttach = self.env['invoice.attachment.master']
        for doc in self.processing_doc_ids:
            attachment = InvoiceAttach.search([
                ('name', '=', doc.name)
            ], limit=1)

            if not attachment:
                attachment = InvoiceAttach.create({
                    'name': doc.name,
                    'bill_type': 'customer',
                })

            attachment_ids.append(attachment.id)

        if attachment_ids:
            invoice_vals['inv_attachment_ids'] = [(6, 0, self.processing_doc_ids.ids)]
        if self.division_id:
            invoice_vals['division_id'] = self.division_id.id

        return invoice_vals

    @api.depends('state', 'order_line.invoice_status')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.
        """
        confirmed_orders = self.filtered(lambda so: so.state == 'sale')
        (self - confirmed_orders).invoice_status = 'no'
        if not confirmed_orders:
            return
        line_invoice_status_all = [
            (order.id, invoice_status)
            for order, invoice_status in self.env['sale.order.line']._read_group([
                ('order_id', 'in', confirmed_orders.ids),
                ('is_downpayment', '=', False),
                ('display_type', '=', False),
            ],
                ['order_id', 'invoice_status'])]
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state != 'sale':
                order.invoice_status = 'no'
            elif order.amount_invoiced > 0 and order.amount_to_invoice != order.amount_total and order.amount_invoiced != order.amount_total:
                order.invoice_status = 'partial'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(
                    invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'

    @api.onchange('partner_id')
    def get_estimation_partner_ids(self):
        # self.payment_term_id = False
        if self.partner_id:
            if self.estimation_id and self.estimation_id.partner_id:
                rebate_list = self.env['res.partner'].search([('parent_id', '=', self.partner_id.id),('customer_rank','>', 0)]).ids
            else:
                rebate_list = self.env['res.partner'].search([]).ids
            # days = self.partner_id.max_payment_days
            #
            # payment_terms = self.env['account.payment.term'].search([
            #     ('days', '<=', days)
            # ])
            #
            # self.verify_payment_term = payment_terms
            self.type_id = self.partner_id.po_type

        else:
            rebate_list = self.env['res.partner'].search([]).ids
            # self.verify_payment_term = False

        self.estimate_partner_ids = [(6, 0, rebate_list)]


    def compute_boe_count(self):
        for rec in self:
            if rec.boe_ids:
                rec.boe_count = len(rec.boe_ids)
            else:
                rec.boe_count = 0

    def compute_bom_count(self):
        for order in self:
            order.bom_count = self.env['mrp.bom'].search_count([('sale_line_id', '=', order.id)])

    def compute_mo_count(self):
        for order in self:
            order.mo_count = self.env['mrp.production'].search_count([('sale_id', '=', order.id)])

    def compute_need_boe(self):
        for rec in self:
            if rec.qtn_so_line_ids and any(not li.product_id for li in rec.qtn_so_line_ids):
                rec.need_boe = True
            else:
                rec.need_boe = False

    def create_boe(self):
        if not self.qtn_approved or self.is_approval_required:
            raise ValidationError("You cannot create BOE this quotation without approval")
        if not self.order_line:
            raise ValidationError("Empty Order Lines: Add items to continue !!")
        if self.is_reject:
            raise ValidationError(_("You cannot create BOE because this quotation has been rejected"))

        if self.order_line:
            lines = []
            for line in self.order_line:
                if line.product_id.detailed_type == 'product' and not line.qtn_line_ids:
                    line_vals = (0, 0, {
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_uom_id': line.product_uom.id,
                        'sale_line_id': line.id
                    })
                    lines.append(line_vals)

        if self.qtn_so_line_ids:
            for vals in self.qtn_so_line_ids:
                product_id = False
                if not vals.product_id:
                    product_id = self.env['product.template'].create({
                        'name': vals.description,
                        'detailed_type': 'product'
                    })
                    vals.product_id = product_id.product_variant_id.id
                elif not vals.product_id.bom_ids:
                    product_id = vals.product_id.product_tmpl_id

                if product_id:
                    boe_vals = {
                        'product_tmpl_id': product_id.id,
                        'product_qty': vals.quantity,
                        'code': self.name,
                        'type': 'normal',
                        'bom_line_ids': lines
                    }
                    boe_id = self.env['mrp.bom'].create(boe_vals)
                    for bom_line in boe_id.bom_line_ids:
                        bom_line.sale_qtn_line_id = vals.id
                        bom_line.sale_line_id.qtn_line_ids = [(4, bom_line.sale_qtn_line_id.id)]
                    vals.boe_id = boe_id.id
                    self.boe_ids |= boe_id

        self.boe_created = True

    # payment_term_id = fields.Many2one("account.payment.term", string="Payment Terms",)



    @api.depends('partner_id')
    def _compute_verify_payment_term(self):
        if self.partner_id:
            days = self.partner_id.max_payment_days

            payment_terms = self.env['account.payment.term'].search([
                ('days', '<=', days)
            ])

            self.verify_payment_term = payment_terms

        else:
            self.verify_payment_term = False

    @api.onchange('company_id')
    def _onchange_company_id_warning(self):
        self.show_update_pricelist = True
        if self.order_line and self.state == 'draft' and not self.opportunity_id:
            return {
                'warning': {
                    'title': _("Warning for the change of your quotation's company"),
                    'message': _("Changing the company of an existing quotation might need some "
                                 "manual adjustments in the details of the lines. You might "
                                 "consider updating the prices."),
                }
            }

    def compute_is_readonly(self):
        for rec in self:
            if rec.invoice_ids:
                rec.is_readonly = True
            else:
                rec.is_readonly = False

    def convert_amount_in_currency(self):
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

    @api.depends('is_product_milestone', 'payment_term_id', 'amount_total')
    def _compute_advance_preview(self):
        for rec in self:
            rec.advance_preview = ""
            if rec.is_product_milestone:
                milestone_preview = ""
                project_milestone_id = self.env['project.milestone'].search([('quantity_percentage', '!=', 0.00)])
                milestone_id = project_milestone_id.filtered(lambda x: x.sale_line_id.order_id.id == rec.id)
                if milestone_id:
                    i = 1
                    for mil in milestone_id:
                        milestone_preview += _(
                            "<b>%(count)s#  </b><b style='color: #704A66;'>%(name)s</b>: <b>%(quantity)s</b> <b>%(precentage)s</b><br/>",
                            count=i,
                            name=mil.name,
                            quantity=int((mil.quantity_percentage) * 100),
                            precentage='%'
                        )
                        i += 1
                rec.advance_preview = milestone_preview
            elif rec.payment_term_id:
                advance_preview = ""
                paytm_id = self.env['account.payment.term'].search(
                    [('id', '=', rec.payment_term_id.id)])
                if paytm_id:
                    currency = self.env.company.currency_id
                    if rec.payment_term_id.early_discount:
                        date = rec.payment_term_id._get_last_discount_date_formatted(
                            rec.date_order.date() or fields.Date.context_today(rec.payment_term_id))
                        discount_amount = rec.payment_term_id._get_amount_due_after_discount(rec.amount_total, 0.0)

                        advance_preview += _(
                            "Early Payment Discount: <b>%(amount)s</b> if paid before <b>%(date)s</b>",
                            amount=formatLang(self.env, discount_amount, monetary=True, currency_obj=currency),
                            date=date,
                        )

                    if not rec.payment_term_id.example_invalid:
                        terms = rec.payment_term_id._compute_terms(
                            date_ref=rec.date_order.date(),
                            currency=currency,
                            company=self.env.company,
                            tax_amount=0,
                            tax_amount_currency=0,
                            sign=1,
                            untaxed_amount=rec.amount_total,
                            untaxed_amount_currency=rec.amount_total,
                        )

                        for i, info_by_dates in enumerate(
                                rec.payment_term_id._get_amount_by_date(terms).values()):
                            date = info_by_dates['date']
                            amount = info_by_dates['amount']
                            advance_preview += "<div style='margin-left: 20px;'>"

                            advance_preview += _(
                                "<b>%(count)s#</b> Terms of <b>%(amount)s</b> on <b style='color: #704A66;'>%(date)s</b>",
                                count=i + 1,
                                amount=formatLang(self.env, amount, monetary=True, currency_obj=currency),
                                date=date,
                            )

                rec.advance_preview = advance_preview
            else:
                rec.advance_preview = ""

    def _compute_survey_start_url(self):
        for rec in self:
            if rec.survey_id:
                rec.survey_start_url = werkzeug.urls.url_join(rec.survey_id.get_base_url(),
                                                              rec.survey_id.get_start_url()) if rec.survey_id else False
            else:
                rec.survey_start_url = False

    def compute_hide_revision_button(self):
        for rec in self:
            rec.hide_revision_button = False
            if rec.picking_ids and any(pick.state == 'done' for pick in rec.picking_ids):
                rec.hide_revision_button = True
            elif rec.invoice_ids and any(inv.state == 'posted' for inv in rec.invoice_ids):
                rec.hide_revision_button = True

    def qtn_approval_request(self):
        self.ensure_one()

        if not self.order_line:
            raise ValidationError(_("Empty Order Lines: Add items to continue!"))

        if not self.qtn_approve_user_ids:
            raise ValidationError(_("Please select Quotation Approval users."))

        # Both must be selected
        if not self.terms_conditions_id or not self.delivery_terms_id:
            raise ValidationError(
                _("Please select both Terms & Conditions and Delivery Terms.")
            )

        # Check for order lines without product (excluding sections/notes)
        invalid_lines = self.order_line.filtered(
            lambda li: not li.display_type
                       and not li.product_id
                       and not li.product_template_id
        )
        if invalid_lines:
            return self.open_order_line_wizard()

        qtn_users = self.qtn_approve_user_ids

        self.qtn_requested = True
        self.show_reject_button = True
        self._action_schedule_activities(qtn_users)

    def action_open_confirm_wizard(self):
        self.ensure_one()
        return {
            'name': 'Update Purchase Reference',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
            }
        }


    lase_revision_number = fields.Many2one("sale.irder", string="Revision Number", tracking=True)

    def _action_schedule_activities(self, qtn_approve_users):
        records = []

        for user in qtn_approve_users:
            record = self.activity_schedule(
                'kg_voyage_marine_sale.quotation_approval_notification',
                user_id=user.id,
                note=f'The user {self.env.user.name} has requested approval for the Quotation {self.name}. Please verify and approve.'
            )
            records.append(record)

        return records

    def qtn_approve(self):
        if not self.order_line:
            raise ValidationError("Empty Order Lines: Add items to continue !!")
        qtn_approve_users = self.qtn_approve_user_ids.ids
        if not qtn_approve_users:
            raise ValidationError(_("Please Select Quotation Approval users"))
        if self.env.user.id not in qtn_approve_users:
            raise UserError(_("You have no access to approve"))
        if self.amount_in_currency > 500000:
            sup_approve_users = self.sup_approve_user_ids.ids
            if not sup_approve_users:
                raise ValidationError(_("Please Select Management users"))

        # if self.order_line and any(
        #         not li.product_id and not li.product_template_id and not li.display_type and not li.code in ['sm', 'fm',
        #                                                                                                      'lm', 'nm',
        #                                                                                                      'cm', 'rm',
        #                                                                                                      'pm', 'om',
        #                                                                                                      'mm',
        #                                                                                                      'em'] for
        #         li in self.order_line):
        #     raise ValidationError(_("Create Product for non inventory items !!"))

        self.qtn_approved = True
        self.qtn_approved_user = self.env.user.id
        self.qtn_requested_approved = True
        self._action_schedule_activities_qtn_approval(qtn_approve_users)
        if self.amount_in_currency >= 100000:
            self.is_approval_required = True
            hod_users = self.hod_approve_user_ids.ids
            if not hod_users:
                raise ValidationError(_("Please Select Head of Department users"))
            self._action_schedule_activities_hod(hod_users)

    def _action_schedule_activities_hod(self, hod_users):
        """
        Schedules activities for the Head of Department approval process.
        """
        for user in hod_users:
            self.activity_schedule(
                'kg_voyage_marine_sale.request_hod_notification',
                user_id=user,
                note=f'The user {self.env.user.name} has approved the quotation and requested the Head of Department to approve Quotation {self.name}. Please verify and approve.'
            )

    def _action_schedule_activities_qtn_approval(self, qtn_approve_users):
        """
        Schedules activities for the quotation approval users.
        """
        request_approval_quotation_activity = self.env.ref('kg_voyage_marine_sale.quotation_approval_notification')
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_approval_quotation_activity and l.user_id != self.env.user
        ).unlink()
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_approval_quotation_activity
        ).action_done()
        for user_id in qtn_approve_users:
            self.activity_schedule(
                'kg_voyage_marine_sale.quotation_approved_notification',
                user_id=user_id,
                note=f'The user {self.env.user.name} has approved for the Quotation {self.name}.'
            )
        approved_quotation_activity = self.env.ref('kg_voyage_marine_sale.quotation_approved_notification')
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == approved_quotation_activity and l.user_id != self.env.user
        ).unlink()
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == approved_quotation_activity
        ).action_done()
        if self.amount_in_currency <= 100000:
            self.hide_reject_button = True

    def hod_approve(self):
        hod_approve_users = self.hod_approve_user_ids.ids
        if not hod_approve_users:
            raise ValidationError(_("Please Select Head of Department users"))

        if self.env.user.id not in hod_approve_users:
            raise UserError(_("You have no access to approve"))
        self.hod_approved = True
        self.hod_approved_user = self.env.user.id
        request_hod_activity = self.env.ref('kg_voyage_marine_sale.request_hod_notification')
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_hod_activity and l.user_id != self.env.user
        ).unlink()
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_hod_activity
        ).action_done()
        self.is_hod_reject = True
        if self.amount_in_currency > 500000:
            print("kkkkkkkkkkkkkkkkkkkk")
            self.is_hod_reject = False
            self.show_reject_button = True
            sup_approve_users = self.sup_approve_user_ids.ids
            if not sup_approve_users:
                raise ValidationError(_("Please Select Management users"))
            self._action_schedule_activities_hod_approve(sup_approve_users)

    def _action_schedule_activities_hod_approve(self, sup_approve_users):
        request_hod_activity = self.env.ref('kg_voyage_marine_sale.request_hod_notification')
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_hod_activity and l.user_id != self.env.user
        ).unlink()
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_hod_activity
        ).action_done()
        if not sup_approve_users:
            raise ValidationError(_("Please Select Management users in Configuration"))
        for user_id in sup_approve_users:
            self.activity_schedule(
                'kg_voyage_marine_sale.request_supervisor_notification',
                user_id=user_id,
                note=f'The user {self.env.user.name} has approved the Head of Department approval and has requested the Management to approve Quotation {self.name}. Please Verify and approve.'
            )

    def supervisor_approve(self):
        print("kkkkkkkkkkkk")
        sup_approve_users = self.sup_approve_user_ids.ids
        if not sup_approve_users:
            raise ValidationError(_("Please Select Management users"))
        if self.env.user.id not in sup_approve_users:
            raise UserError(_("You have no access to approve"))
        self.supervisor_approved = True
        self.supervisor_approved_user = self.env.user.id
        self.is_hod_reject = False
        self.hide_reject_button = True
        self._action_schedule_activities_supervisor_approve(sup_approve_users)

    def _action_schedule_activities_supervisor_approve(self, sup_approve_users):
        request_supervisor_activity = self.env.ref('kg_voyage_marine_sale.request_supervisor_notification')
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_supervisor_activity and l.user_id != self.env.user
        ).unlink()
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_supervisor_activity
        ).action_done()
        for user_id in sup_approve_users:
            self.activity_schedule(
                'kg_voyage_marine_sale.supervisor_approved_notification',
                user_id=user_id,
                note=f'The user {self.env.user.name} has approved the Management approval for the Quotation {self.name}.'
            )
        approved_supervisor_activity = self.env.ref('kg_voyage_marine_sale.supervisor_approved_notification')
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == approved_supervisor_activity and l.user_id != self.env.user
        ).unlink()
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == approved_supervisor_activity
        ).action_done()

    def action_reject(self):
        if not self.qtn_approved and not self.hod_approved or not self.supervisor_approved:
            qtn_approve_users = self.qtn_approve_user_ids.ids

            if self.env.user.id not in qtn_approve_users:
                raise UserError(_("You have no access to reject"))
            self.is_reject = True
            self.qtn_approved = False
            self.hod_approved = True
            self.supervisor_approved = True
            self.show_reject_button = False
            self.state = 'rejected'
            self._action_schedule_activities_action_reject()

        # if self.qtn_approved and not self.hod_approved and not self.supervisor_approved:
        #     hod_approve_users = self.hod_approve_user_ids.ids
        #
        #     if self.env.user.id not in hod_approve_users:
        #         raise UserError(_("You have no access to reject"))

        # if not self.supervisor_approved and self.hod_approved:
        #     sup_approve_users = self.sup_approve_user_ids.ids
        #
        #     if self.env.user.id not in sup_approve_users:
        #         raise UserError(_("You have no access to reject"))



    def _action_schedule_activities_action_reject(self):

        self.activity_schedule('kg_voyage_marine_sale.reject_quotation_notification',
                               user_id=self.create_uid.id,
                               note=f' The user {self.env.user.name}  has rejected the approval of the Quotation {self.name}.')

        reject_approved_activity = self.env.ref('kg_voyage_marine_sale.reject_quotation_notification')

        self.activity_ids.filtered(
            lambda l: l.activity_type_id == reject_approved_activity and l.user_id != self.env.user).unlink()

        self.activity_ids.filtered(lambda l: l.activity_type_id == reject_approved_activity).action_done()

        request_supervisor_activity = self.env.ref('kg_voyage_marine_sale.request_supervisor_notification')

        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_supervisor_activity).unlink()

        request_hod_activity = self.env.ref('kg_voyage_marine_sale.request_hod_notification')

        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_hod_activity).unlink()

        request_approval_quotation_activity = self.env.ref('kg_voyage_marine_sale.quotation_approval_notification')

        self.activity_ids.filtered(lambda
                                       l: l.activity_type_id == request_approval_quotation_activity).unlink()

    def kg_reject(self):
        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'revision.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
                'default_is_reject': True,
            }
        }

    def kg_non_inventory_product_ml(self):
        return {
            'name': 'Manufaction prdouct for non inventory iteam',
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_type': 'product',
                'default_uom': 'unit',
            }
        }

    def open_order_line_wizard(self):
        self.ensure_one()

        # Find matching lines
        matching_lines = self.order_line.filtered(
            lambda li: not li.product_id and not li.product_template_id and not li.display_type
        )

        # Create wizard record
        wizard = self.env['order.line.wizard'].create({
            'order_line_ids': [(0, 0, {'order_line_id': line.id}) for line in matching_lines],
            # Convert list to string
        })

        # Return action to open the wizard
        return {
            'name': 'Manufacturing Product for Non-Inventory Items',
            'type': 'ir.actions.act_window',
            'res_model': 'order.line.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

    def action_confirm(self):
        if not self.qtn_approved:
            raise ValidationError("You cannot confirm this quotation without approval")
        if not self.order_line:
            raise ValidationError("Empty Order Lines: Add items to continue !!")
        if self.is_reject:
            raise ValidationError(_("You cannot confirm because this quotation has been rejected"))
        if not self.boe_created and self.need_boe:
            raise ValidationError(_("Create a BOE and continue !!"))
        if not self.quotation_reference:
            self.quotation_reference = self.name
        if not self.purchase_reference:
            return self.action_open_confirm_wizard()
        for line in self.order_line:
            if line.product_template_id.is_equipment and not line.is_jobsheet:
                raise ValidationError(
                    _("Please enable the create calibration button for the product: %s" % line.product_id.name))
        # for rec in self:
        #     if rec.amount_total and rec.estimation_id:
        #         # Check only main lines (not subitems)
        #         non_subitems = rec.order_line.filtered(lambda l: not l.is_subitem)
        #         if non_subitems and rec.amount_total < rec.estimation_id.total:
        #             raise UserError(
        #                 "Selling Price cannot be less than Estimation Cost.\n\nEstimation Cost is %.2f %s\nOrder: %s" % (
        #                     rec.estimation_id.total, rec.estimation_id.currency_id.name, rec.name))

        if not self.so_confirmed:
            qtn_date = self.date_order
            year, month = qtn_date.strftime('%y'), qtn_date.strftime('%m')
            sequence_number = self.division_id.so_sequence_id.next_by_id()
            division_name = self.division_id.division
            self.name = f"{division_name}{year}{month}{sequence_number}"

        self.so_confirmed = True

        if not self.so_reference:
            self.so_reference = self.name
        else:
            self.name = self.so_reference

        if self.order_line and any(line.is_fl for line in self.order_line):
            missing_config_products = []
            for line in self.order_line:
                if (
                        line.is_fl and line.code == 'ft' and
                        (line.product_id.detailed_type != 'service' or
                         line.product_id.service_tracking != 'task_in_project')
                ):
                    missing_config_products.append(line.product_id.display_name)

            if missing_config_products:
                product_names_str = ", ".join(missing_config_products)
                raise UserError(
                    _("Please configure the project base for the following products in FL: %s") % product_names_str
                )

        if self.order_line and any(
                not li.product_id and not li.product_template_id and not li.display_type for li in
                self.order_line):
            matching_lines = [
                (li.id, li.name) for li in self.order_line
                if not li.product_id and not li.product_template_id and not li.display_type
            ]

            return self.open_order_line_wizard()

        # if self.order_line and any(line.is_fl for line in self.order_line):
        #     missing_config_products = []
        #     for line in self.order_line:
        #         if (
        #                 line.is_fl and
        #                 (line.product_id.detailed_type != 'service' or
        #                  line.product_id.service_tracking != 'task_in_project')
        #         ):
        #             missing_config_products.append(line.product_id.display_name)
        #
        #     if missing_config_products:
        #         product_names_str = ", ".join(missing_config_products)
        #         raise UserError(
        #             _("Please configure the project base for the following products in FL: %s") % product_names_str
        #         )
        #
        # if self.order_line and any(
        #         not li.product_id and not li.product_template_id and li.code in ['sm', 'fm', 'lm', 'nm', 'cm', 'rm',
        #                                                                          'pm', 'om', 'mm',
        #                                                                          'em'] and not li.display_type for li in
        #         self.order_line):
        #     matching_lines = [
        #         (li.id, li.name) for li in self.order_line
        #         if not li.product_id and not li.product_template_id and li.code in ['sm', 'fm', 'lm', 'nm', 'cm', 'rm',
        #                                                                             'pm', 'om', 'mm',
        #                                                                             'em'] and not li.display_type
        #     ]
        #
        #     return self.open_order_line_wizard()
        else:
            if self.order_line and any(
                    not li.product_id and not li.product_template_id and not li.display_type for li in self.order_line):
                raise ValidationError(_("Create Product for non inventory items !!"))

            res = super(KGSaleOrderInherit, self).action_confirm()

            service_sol_id = self.order_line.filtered(lambda x: x.product_id.detailed_type == 'service')

            if self.picking_ids:
                for picking in self.picking_ids:
                    picking.boe_ids = self.boe_ids.ids
                    picking.vessel_id = self.vessel_id.id
                    picking.so_ids = [(6, 0, self.ids)]
                    picking.partner_shipping_id = self.partner_shipping_id.id
                    picking.partner_invoice_id = self.partner_invoice_id.id
                    picking.customer_ref = self.customer_reference

                    order_lines = []
                    if self.qtn_so_line_ids:
                        for qtn_line in self.qtn_so_line_ids:
                            line_vals = (0, 0, {
                                'product_id': qtn_line.product_id.id,
                                'description': qtn_line.description,
                                'quantity': qtn_line.quantity,
                                'uom_id': qtn_line.uom_id.id,
                                'boe_id': qtn_line.boe_id.id
                            })
                            order_lines.append(line_vals)

                    service_lines = []
                    if service_sol_id:
                        for serv in service_sol_id:
                            serv_vals = (0, 0, {
                                'product_id': serv.product_id.id,
                                'description': serv.name,
                                'qty': serv.product_uom_qty,
                                'uom_id': serv.product_uom.id,
                                'so_id': serv.order_id.id,
                                'so_line_id': serv.id,
                            })
                            service_lines.append(serv_vals)

                    picking.write({
                        'main_product_line_ids': order_lines,
                        'service_product_line_ids': service_lines
                    })
            for rec in self.order_line:
                if rec.code in ['sm', 'fm', 'lm', 'nm', 'cm', 'rm', 'pm', 'om', 'mm', 'em'] and not rec.is_subitem:
                    main_line_id = rec

                    if not main_line_id:
                        continue
                    print(main_line_id, "main_line_id")
                    print(main_line_id.product_template_id, "main_line_id.product_template_id")

                    direct_from_so_matching_order_lines = self.order_line.filtered(
                        lambda l: l.main_line_id == main_line_id
                    )
                    estimation_matching_order_lines = self.order_line.filtered(
                        lambda l: l.manin_product_order_line_id == main_line_id
                    )
                    print(direct_from_so_matching_order_lines, "matching_order_lines")
                    matching_order_lines = direct_from_so_matching_order_lines | estimation_matching_order_lines
                    print(matching_order_lines, "matching_order_lines")

                    material_cost = {}
                    for sub_item in matching_order_lines :
                        print(sub_item, "sub_item")
                        product_id = sub_item.product_id.id
                        quantity = sub_item.product_uom_qty
                        code = sub_item.code
                        unit_price = sub_item.sub_item_price
                        print(unit_price,"unit_price")

                        # If the product already exists, add the quantities together
                        if product_id in material_cost:
                            material_cost[product_id]['quantity'] += quantity
                        else:
                            material_cost[product_id] = {
                                'quantity': quantity,
                                'code': code,
                                'unit_price':unit_price
                            }

                    mo_lines = []
                    for product_id, vals in material_cost.items():
                        quantity = vals['quantity']
                        code = vals['code']
                        unit_price = vals['unit_price']

                        mo_lines.append((0, 0, {
                            'product_id': product_id,
                            'product_uom_qty': quantity,
                            'code': code,
                            'unit_price': unit_price,
                        }))

                    product_tmpl_id = main_line_id.product_template_id.id or main_line_id.product_id.product_tmpl_id.id
                    existing_bom = self.env['mrp.bom'].search([
                        ('product_tmpl_id', '=', product_tmpl_id)
                    ], limit=1, order='id asc')

                    bom = False
                    if not existing_bom and matching_order_lines:
                        bom_lines = []
                        for product_id, vals in material_cost.items():
                            quantity = vals['quantity']
                            code = vals['code']
                            unit_price = vals['unit_price']
                            bom_lines.append((0, 0, {
                                'product_id': product_id,
                                'product_qty': quantity,
                                'code': code,
                                'unit_price':unit_price
                            }))
                        bom = self.env["mrp.bom"].create({
                            'product_tmpl_id': product_tmpl_id,
                            'company_id': self.env.user.company_id.id,
                            'bom_line_ids': bom_lines,
                        })
                    if not existing_bom and not bom:
                        raise ValidationError(
                            f"No Bill of Materials found or created for product: {main_line_id.product_id.display_name}"
                        )

                    # Create Manufacturing Order
                    mo = self.env["mrp.production"].create({
                        "product_id": main_line_id.product_id.id,
                        "origin": self.name,
                        "company_id": self.env.user.company_id.id,
                        "product_qty": main_line_id.product_uom_qty or 1,
                        "sale_id": self.id,
                        'move_raw_ids': mo_lines if rec else [],
                        "bom_id": existing_bom.id if existing_bom else (bom.id if bom else False),
                    })
                    mo.origin = self.name
                    main_line_id.product_id.is_manufactured_product = True

            # for rec in self.order_line:
            #
            #     if rec.code in ['sm', 'fm', 'lm', 'nm', 'cm', 'rm', 'pm', 'om', 'mm', 'em'] and (
            #             rec.main_line_id
            #     ):
            #         labour_cost = {}
            #         material_cost = {}
            #         other_cost = {}
            #         item = {}
            #
            #         if rec.labour_id:
            #             for sub_item in rec.labour_id.sub_item_ids:
            #                 product_id = sub_item.product_id.id
            #                 quantity = sub_item.quantity
            #                 code = sub_item.code
            #                 labour_cost[product_id] = quantity
            #
            #             mo_lines = []
            #             for product_id, quantity in labour_cost.items():
            #                 mo_lines.append(
            #                     (0, 0, {
            #                         'product_id': product_id,
            #                         'product_uom_qty': quantity,
            #                         'code': code
            #                     })
            #                 )
            #
            #             existing_bom = self.env['mrp.bom'].search([
            #                 ('product_tmpl_id', '=',
            #                  rec.product_template_id.id if rec.product_template_id.id else rec.product_id.id)
            #             ], limit=1,order='id asc')
            #             print(existing_bom, "existing_bom")
            #
            #             if existing_bom:
            #                 bom_lines = []
            #                 for product_id, quantity in labour_cost.items():
            #                     bom_lines.append(
            #                         (0, 0, {
            #                             'product_id': product_id,
            #                             'product_qty': quantity,
            #                             'code': code
            #                             # 'product_uom_id': self.env['product.product'].browse(product_id).uom_id.id,  # Uncomment if you need to link UOM
            #                         })
            #                     )
            #             else:
            #                 bom_lines = []
            #                 for product_id, quantity in labour_cost.items():
            #                     bom_lines.append(
            #                         (0, 0, {
            #                             'product_id': product_id,
            #                             'product_qty': quantity,
            #                             'code': code
            #                             # 'product_uom_id': self.env['product.product'].browse(product_id).uom_id.id,  # Uncomment if you need to link UOM
            #                         })
            #                     )
            #
            #                 bom = self.env["mrp.bom"].create(
            #                     {
            #                         'product_tmpl_id': rec.product_template_id.id if rec.product_template_id.id else rec.product_id.id,
            #                         'company_id': self.env.user.company_id.id,
            #                         'bom_line_ids': bom_lines,
            #                     }
            #                 )
            #                 print(bom, "created_bom")
            #
            #             mo = self.env["mrp.production"].create(
            #                 {
            #                     "product_id": rec.product_id.id if rec.product_template_id.id else rec.product_id.id,
            #                     # "product_uom_id": rec.product_uom.id,
            #                     "origin": self.name,
            #                     'company_id': self.env.user.company_id.id,
            #                     "product_qty": rec.labour_id.quantity if rec.labour_id.quantity else 1,
            #                     "sale_id": self.id,
            #                     # 'move_raw_ids': mo_lines if rec.labour_id.sub_item_ids else [],
            #                     'bom_id': existing_bom.id if existing_bom else bom.id,
            #                 }
            #             )
            #             mo.origin = self.name
            #
            #         # if rec.material_cost_id:
            #         #
            #         #     for sub_item in rec.material_cost_id.sub_item_ids:
            #         #         product_id = sub_item.product_id.id
            #         #         quantity = sub_item.quantity
            #         #         code = sub_item.code
            #         #         material_cost[product_id] = quantity
            #         #
            #         #     mo_lines = []
            #         #     for product_id, quantity in material_cost.items():
            #         #         mo_lines.append(
            #         #             (0, 0, {
            #         #                 'product_id': product_id,
            #         #                 'product_uom_qty': quantity,
            #         #                 'code': code
            #         #             })
            #         #         )
            #         #     existing_bom = self.env['mrp.bom'].search([
            #         #         ('product_tmpl_id', '=',
            #         #          rec.product_template_id.id if rec.product_template_id.id else rec.product_id.id)
            #         #     ], limit=1,order='id asc')
            #         #     print(existing_bom, "existing_bom")
            #         #
            #         #     if existing_bom:
            #         #         bom_lines = []
            #         #         for product_id, quantity in material_cost.items():
            #         #             bom_lines.append(
            #         #                 (0, 0, {
            #         #                     'product_id': product_id,
            #         #                     'product_qty': quantity,
            #         #                     'code': code
            #         #                     # 'product_uom_id': self.env['product.product'].browse(product_id).uom_id.id,
            #         #                 })
            #         #             )
            #         #
            #         #     else:
            #         #         bom_lines = []
            #         #         for product_id, quantity in material_cost.items():
            #         #             bom_lines.append(
            #         #                 (0, 0, {
            #         #                     'product_id': product_id,
            #         #                     'product_qty': quantity,
            #         #                     'code': code
            #         #                     # 'product_uom_id': self.env['product.product'].browse(product_id).uom_id.id,
            #         #                 })
            #         #             )
            #         #         bom = self.env["mrp.bom"].create(
            #         #             {
            #         #                 'product_tmpl_id': rec.product_template_id.id if rec.product_template_id.id else rec.product_id.id,
            #         #                 'company_id': self.env.user.company_id.id,
            #         #                 'product_qty': rec.material_cost_id.quantity if rec.material_cost_id.quantity else 1,
            #         #                 'bom_line_ids': bom_lines if bom_lines else [] ,
            #         #
            #         #             }
            #         #         )
            #         #
            #         #     mo = self.env["mrp.production"].create(
            #         #         {
            #         #             "product_id": rec.product_id.id if rec.product_template_id.id else rec.product_id.id,
            #         #             # "product_uom_id": rec.product_uom.id,
            #         #             "origin": self.name,
            #         #             'company_id': self.env.user.company_id.id,
            #         #             "product_qty": rec.material_cost_id.quantity if rec.material_cost_id.quantity else 1,
            #         #             "sale_id": self.id,
            #         #             'bom_id': existing_bom.id if existing_bom else bom.id,
            #         #             # 'move_raw_ids': mo_lines if rec.material_cost_id.sub_item_ids else [],
            #         #         }
            #         #     )
            #         #     mo.origin = self.name
            #         if rec.material_cost_id:
            #
            #             material_cost = {}
            #
            #             for sub_item in rec.material_cost_id.sub_item_ids:
            #                 product_id = sub_item.product_id.id
            #                 quantity = sub_item.quantity
            #                 code = sub_item.code
            #                 material_cost[product_id] = quantity
            #
            #             mo_lines = []
            #             for product_id, quantity in material_cost.items():
            #                 mo_lines.append(
            #                     (0, 0, {
            #                         'product_id': product_id,
            #                         'product_uom_qty': quantity,
            #                         'code': code
            #                     })
            #                 )
            #
            #             # Search for an existing BOM
            #             existing_bom = self.env['mrp.bom'].search([
            #                 ('product_tmpl_id', '=',
            #                  rec.product_template_id.id if rec.product_template_id.id else rec.product_id.product_tmpl_id.id)
            #             ], limit=1, order='id asc')
            #
            #             print(existing_bom, "existing_bom")
            #
            #             # Initialize BOM variable
            #             bom = False
            #
            #             # If BOM does not exist, and sub items are available, create BOM
            #             if not existing_bom and rec.material_cost_id.sub_item_ids:
            #                 bom_lines = []
            #                 for product_id, quantity in material_cost.items():
            #                     bom_lines.append(
            #                         (0, 0, {
            #                             'product_id': product_id,
            #                             'product_qty': quantity,
            #                             'code': code
            #                         })
            #                     )
            #
            #                 bom = self.env["mrp.bom"].create({
            #                     'product_tmpl_id': rec.product_template_id.id if rec.product_template_id.id else rec.product_id.product_tmpl_id.id,
            #                     'company_id': self.env.user.company_id.id,
            #                     'product_qty': rec.material_cost_id.quantity or 1,
            #                     'bom_line_ids': bom_lines,
            #                 })
            #
            #             # Create MRP Production Order
            #             mo = self.env["mrp.production"].create({
            #                 "product_id": rec.product_id.id,
            #                 "origin": self.name,
            #                 'company_id': self.env.user.company_id.id,
            #                 "product_qty": rec.material_cost_id.quantity or 1,
            #                 "sale_id": self.id,
            #                 'bom_id': existing_bom.id if existing_bom else (bom.id if bom else False),
            #             })
            #
            #             mo.origin = self.name
            #             rec.product_id.is_manufactured_product = True
            #
            #         if rec.other_cost_id:
            #
            #             for sub_item in rec.other_cost_id.sub_item_ids:
            #                 product_id = sub_item.product_id.id
            #                 quantity = sub_item.quantity
            #                 code = sub_item.code
            #                 other_cost[product_id] = quantity
            #
            #             mo_lines = []
            #             for product_id, quantity in other_cost.items():
            #                 mo_lines.append(
            #                     (0, 0, {
            #                         'product_id': product_id,
            #                         'product_uom_qty': quantity,
            #                         'code': code
            #                     })
            #                 )
            #             existing_bom = self.env['mrp.bom'].search([
            #                 ('product_tmpl_id', '=',
            #                  rec.product_template_id.id if rec.product_template_id.id else rec.product_id.id)
            #             ], limit=1 ,order='id asc')
            #
            #             if existing_bom:
            #                 bom_lines = []
            #                 for product_id, quantity in other_cost.items():
            #                     bom_lines.append(
            #                         (0, 0, {
            #                             'product_id': product_id,
            #                             'product_qty': quantity,
            #                             'code':code
            #                             # 'product_uom_id': self.env['product.product'].browse(product_id).uom_id.id,  # Uncomment if you need to link UOM
            #                         })
            #                     )
            #             else:
            #                 bom_lines = []
            #                 for product_id, quantity in other_cost.items():
            #                     bom_lines.append(
            #                         (0, 0, {
            #                             'product_id': product_id,
            #                             'product_qty': quantity,
            #                             'code': code
            #                             # 'product_uom_id': self.env['product.product'].browse(product_id).uom_id.id,  # Uncomment if you need to link UOM
            #                         })
            #                     )
            #                 bom = self.env["mrp.bom"].create(
            #                     {
            #                         'product_tmpl_id': rec.product_template_id.id if rec.product_template_id.id else rec.product_id.id,
            #                         'company_id': self.env.user.company_id.id,
            #                         'bom_line_ids': bom_lines,
            #
            #                     }
            #                 )
            #             mo_values = {
            #                 "product_id": rec.product_id.id if rec.product_template_id.id else rec.product_id.id,
            #                 # "product_uom_id": rec.product_uom.id,
            #                 "origin": self.name,
            #                 'company_id': self.env.user.company_id.id,
            #                 "product_qty": rec.other_cost_id.quantity if rec.other_cost_id.quantity else 1,
            #                 "sale_id": self.id,
            #                 # 'move_raw_ids': mo_lines if rec.other_cost_id.sub_item_ids else [],
            #                 'bom_id': existing_bom.id if existing_bom else bom.id,
            #             }
            #
            #             mo = self.env["mrp.production"].create(mo_values)
            #             mo.origin = self.name
            #
            #         if rec.item_id:
            #             for sub_item in rec.item_id.sub_item_ids:
            #                 product_id = sub_item.product_id.id
            #                 quantity = sub_item.quantity
            #                 code = sub_item.code
            #                 item[product_id] = quantity
            #             mo_lines = []
            #             for product_id, quantity in item.items():
            #                 mo_lines.append(
            #                     (0, 0, {
            #                         'product_id': product_id,
            #                         'product_uom_qty': quantity,
            #                         'code': code
            #                     })
            #                 )
            #             product_tmpl_id = rec.product_template_id.id if rec.product_template_id.id else rec.product_id.id
            #
            #             bom_lines = []
            #             for product_id, quantity in item.items():
            #                 bom_lines.append(
            #                     (0, 0, {
            #                         'product_id': product_id,
            #                         'product_qty': quantity,
            #                         'code': code
            #                         # 'product_uom_id': self.env['product.product'].browse(product_id).uom_id.id,
            #                     })
            #                 )
            #             boe_vals = {
            #                     'product_tmpl_id': product_tmpl_id,
            #                     'company_id': self.env.user.company_id.id,
            #                     'bom_line_ids': bom_lines,
            #                 }
            #
            #             boe_id = self.env['mrp.bom'].create(boe_vals)
            #             values1 = {
            #                 "product_id": rec.product_id.id if rec.product_template_id.id else rec.product_id.id,
            #                 # "product_uom_id": rec.product_uom.id,
            #                 "origin": self.name,
            #                 'company_id': self.env.user.company_id.id,
            #                 "product_qty": rec.item_id.quantity if rec.item_id.quantity else 1,
            #                 "sale_id": self.id,
            #                 "move_raw_ids": mo_lines if rec.item_id.sub_item_ids else [],
            #                 'bom_id': boe_id.id,
            #             }
            #
            #             mo = self.env["mrp.production"].create(values1)
            #             mo.origin = self.name

            return res

    def action_view_mo(self):
        return {
            'name': 'Bill of Material',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('sale_id', '=', self.id)],
        }

    def action_view_bom(self):
        return {
            'name': 'Bill of Material',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'view_mode': 'tree,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('sale_line_id', '=', self.id)],
        }

    @api.onchange('division_id')
    def restrict_division(self):
        for rec in self:
            if rec.estimation_id:
                raise ValidationError(
                    _("If a quotation is generated through an estimation; it can't be revised with division, if there are any changes, cancel the estmation and proceed with a new estimation."))

    @api.onchange('pricelist_id')
    def restrict_pricelist(self):
        for rec in self:
            if rec.estimation_id:
                raise ValidationError(
                    _("If a quotation is generated through an estimation; it can't be revised with pricelist, if there are any changes, cancel the estmation and proceed with a new estimation."))

    def revision_reason(self):
        print("rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr")
        return {
            'name': 'Revision Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'revision.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
            }
        }

    def action_view_revisions(self):
        return {
            'name': 'Revisions Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('state', '=', 'cancel'), ('id', 'in', self.revision_ids.ids)],
        }

    def action_view_boe(self):
        return {
            'name': 'Bill of Material',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.bom',
            'view_mode': 'tree,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('id', 'in', self.boe_ids.ids)],
        }

    def get_mr_ids(self):
        return {
            'name': 'Material Issues',
            'type': 'ir.actions.act_window',
            'res_model': 'material.purchase.requisition',
            'view_mode': 'tree,form',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('id', 'in', self.mr_ids.ids)],
        }

    # from odoo.exceptions import UserError

    def action_delivery_note(self):
        for order in self:
            picking_type = self.env.ref('stock.picking_type_out', raise_if_not_found=False)
            used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations', raise_if_not_found=False)

            if not picking_type or not used_location:
                raise UserError('Required picking type or location is missing.')

            dest_location = order.partner_id.property_stock_customer
            dev_seq = self.env['ir.sequence'].next_by_code('do.seq') or '/'

            name = f"DN_{used_location.name}{dev_seq}"

            # Create picking
            picking = self.env['stock.picking'].create({
                'name': name,
                'partner_id': order.partner_id.id,
                'picking_type_id': picking_type.id,
                'location_id': used_location.id,
                'location_dest_id': dest_location.id,
                'move_type': 'direct',
                'origin': order.name,
            })

            for line in order.order_line:
                if line.product_id and line.product_uom_qty > 0 and line.is_jobsheet:
                    self.env['stock.move'].create({
                        'name': line.name or line.product_id.name,
                        'description_picking': line.name or line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'location_id': used_location.id,
                        'location_dest_id': dest_location.id,
                        'picking_id': picking.id,
                    })

        return True
        # # Create the move to unscrap the product and move back to the customer location
        # unscrap_move = self.env['stock.move'].create({
        #     'name': 'Unscrap: %s' % order_line.product_id.name,  # Name for the move
        #     # 'location_id': order_line.order_id.warehouse_id.lot_stock_id.id,  # From stock location
        #     # 'location_dest_id': order_line.order_id.partner_id.property_stock_customer.id,
        #     # To customer (destination location)
        #     'product_id': order_line.product_id.id,  # The product to be moved
        #     'product_uom': order_line.product_uom.id,  # UOM for the product
        #     'picking_id': unscrap_picking.id,  # Link the move to the picking
        #     'product_uom_qty': order_line.product_uom_qty,  # The quantity from the order line
        #     'state': 'draft',  # Initial state is draft
        # })
        # for order in self.order_line:
        #
        #     pickings = self.env['stock.picking'].search([
        #         ('sale_id', '=', self.id),
        #         ('state', 'not in', ['cancel', 'done']),
        #     ])
        #
        #     for picking in pickings:
        #         # You can either cancel the picking or make it draft
        #         # To stop the picking, you might want to cancel it or reset it to draft
        #         if picking.state == 'assigned':
        #             picking.action_cancel()  # Cancel the picking if it's already assigned
        #
        #         elif picking.state == 'draft':
        #             picking.action_confirm()  # If it's draft, you could confirm again or simply leave it
        #
        #         # Alternatively, you can use other states like 'waiting' based on your workflow
        #         # Make sure to adjust this according to your actual workflow logic.

        # return True

    # @api.onchange('partner_id')
    # def get_values_from_partner(self):
    #     for rec in self:
    #         if rec.partner_id and rec.partner_id.po_attach_files:
    #             rec.po_attach_files = rec.partner_id.po_attach_files
    #         else:
    #             rec.po_attach_files = False
    #
    #         if rec.partner_id and rec.partner_id.child_ids:
    #             child_ids = rec.partner_id.child_ids
    #             default_attn = child_ids.filtered(lambda x: x.is_default_attn)
    #             non_default_attn = child_ids.filtered(lambda x: not x.is_default_attn)
    #
    #             rec.attention = (default_attn or non_default_attn or child_ids)[0].id

    def action_cancel(self):
        res = super(KGSaleOrderInherit, self).action_cancel()

        if self.survey_id and self.survey_start_url:
            template_id = self.env.ref("kg_voyage_marine_sale.kg_feedback_survey_mail")
            template_id.send_mail(self.id, force_send=True)

        self.hide_reject_button = True

        return res

    def action_draft(self):
        # if self.customer_reference:
        #     raise ValidationError(_("Cannot proceed with 'Set to Quotation' Customer Reference has been entered."))
        if self.purchase_reference:
            raise ValidationError(_("Cannot proceed with 'Set to Quotation' Purchase Reference has been entered."))
        res = super(KGSaleOrderInherit, self).action_draft()
        self.qtn_requested = False
        self.qtn_approved = False
        self.is_approval_required = False
        self.is_reject = False
        self.show_reject_button = False
        self.hod_approved = False
        self.supervisor_approved = False
        self.hide_reject_button = False
        self.qtn_requested_approved = False


        if self.so_confirmed:
            if not self.main_revision_id:
                if self.quotation_reference:
                    self.name = self.quotation_reference
            else:
                revision_ids = self.env['sale.order'].search([('main_revision_id', '=', self.main_revision_id.id)])
                if revision_ids:
                    revision_count = len(revision_ids)
                    revision_count = revision_count - 1
                    if self.without_revision_qtn and revision_count:
                        self.name = self.without_revision_qtn + '_R' + str(revision_count)
            # if self.main_revision_id:

            #     else:
            #         if self.quotation_reference:
            #             self.name = self.quotation_reference
        else:
            self.name = self.name
        return res

    def get_estimation(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CRM Estimation',
            'view_mode': 'tree,form',
            'res_model': 'crm.estimation',
            'domain': [('id', '=', self.estimation_id.id)],
            'context': {'create': False}
        }

    def action_preview_sale_order(self):
        if self.state in ['sale','done']:
            return {
                'target': 'new',
                'type': 'ir.actions.act_url',
                'url': '/report/pdf/sale_pdf_quote_builder.action_report_saleorder_raw/%s' % self.id
            }
        else:
            return {
                'target': 'new',
                'type': 'ir.actions.act_url',
                'url': '/report/pdf/kg_voyage_marine_sale.action_quotation_report/%s' % self.id
            }

    # @api.constrains('amount_total', 'estimation_id')
    # def verify_sales_estimation_cost(self):
    #     for rec in self:
    #         if rec.amount_total and rec.estimation_id:
    #             # Check only main lines (not subitems)
    #             non_subitems = rec.order_line.filtered(lambda l: not l.is_subitem)
    #             if non_subitems and rec.amount_total < rec.estimation_id.total:
    #                 raise ValidationError(
    #                     "Selling Price cannot be less than Estimation Cost.\n\t Estimation Cost is %.2f %s %s" % (
    #                         rec.estimation_id.total, rec.estimation_id.currency_id.name, rec.name))

    def request_revision(self):
        rev_approve_users = self.env['ir.config_parameter'].get_param('kg_voyage_marine_sale.sale_revision_users_ids',
                                                                      False)

        if not rev_approve_users or rev_approve_users == '[]':
            raise ValidationError(_("Please Select Revision Approval users in Configuration"))

        self.requested_revision = True

    def approve_revision(self):
        rev_approve_users = self.env['ir.config_parameter'].get_param(
            'kg_voyage_marine_sale.sale_revision_users_ids', False)

        if self.env.user.id not in literal_eval(rev_approve_users):
            raise UserError(_("You have no access to approve"))

        self.approved_revision = True

    def add_section(self):
        return {
            'name': 'Add a Section',
            'type': 'ir.actions.act_window',
            'res_model': 'add.section.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
            }
        }

    def edit_section(self):
        sol_ids = self.order_line.filtered(lambda x: x.display_type == 'line_section')

        return {
            'name': 'Edit a Section',
            'type': 'ir.actions.act_window',
            'res_model': 'edit.section.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
                'default_sol_ids': [(6, 0, sol_ids.ids)],
            }
        }

    def create_pro_inv(self):
        self.proforma_invoice_no = self.env['ir.sequence'].next_by_code('proforma.inv')

    def action_quotation_send(self):
        res = super(KGSaleOrderInherit, self).action_quotation_send()
        # if res and self.state == 'draft':
        #     self.proforma_invoice_no = self.env['ir.sequence'].next_by_code('proforma.inv')
        if self.env.context.get('proforma'):
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf("sale.action_report_pro_forma_invoice",
                                                                            [self.id])
            file_name = str('PRO-FORMA-') + str(self.name)
        else:
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf("kg_voyage_marine_sale.action_quotation_report", [self.id])
            if self.state in ['draft', 'sent']:
                file_name = str('Quotation-') + str(self.name)
            else:
                file_name = str('Order-') + str(self.name)

        if isinstance(pdf_content, bytes):
            encoded_pdf = base64.b64encode(pdf_content)

            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': encoded_pdf.decode(),
                'res_model': 'sale.order',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })

            if 'context' in res:
                res['context']['default_attachment_ids'] = [(4, attachment.id)]

            else:
                res['context'] = {'default_attachment_ids': [(4, attachment.id)]}

        return res

    def action_print_dn(self):
        product_ids = self.env['product.product']
        so_ids = self.env['sale.order'].browse(self._context.get('active_ids'))
        if len(so_ids) > 1:
            raise ValidationError(_("This option is only available for a single sale order"))
        else:
            for li in so_ids:
                if li.order_line:
                    product_ids |= li.order_line.filtered(lambda x: not x.display_type).mapped('product_id')
            return {
                'name': 'Select Products',
                'type': 'ir.actions.act_window',
                'res_model': 'dn.select.products',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_so_id': so_ids[0].id if so_ids else False,
                    'default_dn_product_ids': [(6, 0, product_ids.ids)],
                    'default_product_ids': [(6, 0, product_ids.ids)],
                }
            }

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        InvoiceAttach = self.env['invoice.attachment.master']
        for sale in self:
            for move in moves.filtered(lambda m: m.invoice_origin == sale.name):

                move.vessel_id = sale.vessel_id.id
                move.sale_id = sale.id

                attachment_ids = []

                for doc in sale.processing_doc_ids:
                    attachment = InvoiceAttach.search([
                        ('name', '=', doc.name)
                    ], limit=1)

                    if not attachment:
                        attachment = InvoiceAttach.create({
                            'name': doc.name,
                            'bill_type': 'customer',
                        })

                    attachment_ids.append(attachment.id)

                if attachment_ids:
                    move.inv_attachment_ids = [(6, 0, attachment_ids)]

        return moves


class KGChecklistName(models.Model):
    _name = "checklist.name"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Checklist Name"

    name = fields.Char(string="Name", required=True, copy=False)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)


class KGChecklistLines(models.Model):
    _name = "checklist.lines"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Checklist Lines"

    name = fields.Char(string="Name")
    processing_document_id = fields.Many2one("processing.documents", string="Processing Documents")
    checklist_name_id = fields.Many2one("checklist.name", string="Checklist Names")
    checkbox = fields.Boolean(default=False, string="Is Attached")
    so_id = fields.Many2one("sale.order", string="SO")
    attachment = fields.Binary(
        string="Document Attachment",
    )
    attachment_filename = fields.Char(
        string="File Name"
    )
    doc_attach_ids = fields.Many2many('ir.attachment',
                                      relation='doc_attachment_ids', column='attach_id3',
                                      column2='doc_id',
                                      string="Attachment")


    @api.model
    def create(self, vals):
        if vals.get('doc_attach_ids'):
            command = vals.get('doc_attach_ids')[0]
            if command[0] == 6 and command[2]:  # (6, 0, [ids])
                vals['checkbox'] = True
            else:
                vals['checkbox'] = False
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)

        if 'doc_attach_ids' in vals:
            for rec in self:
                if rec.doc_attach_ids:
                    rec.checkbox = True
                else:
                    rec.checkbox = False

        return res


class KGCRMEstimationInherit(models.Model):
    _inherit = "crm.estimation"

    division_id = fields.Many2one("kg.divisions", string="Division")

    @api.model_create_multi
    def create(self, vals):
        for i in vals:
            sequence = self.env['ir.sequence'].next_by_code('kg.crm.estimation')
            division_id = i.get('division_id')
            if division_id:
                division_record = self.env['kg.divisions'].browse(division_id)
                division_name = division_record.division
                first_letter = division_name[0].upper() if division_name else ''
                i['name'] = f"EST_{first_letter}{sequence}"

        return super(KGCRMEstimationInherit, self).create(vals)


    def kg_action_create_rfq(self):
        active_id = self.env['crm.estimation'].browse(self._context.get('active_ids'))

        if not active_id or len(active_id) != 1:
            raise ValidationError(_("Please select exactly one estimation."))

        active_id = active_id[0]
        orderline = []
        has_any = False
        for line in active_id.material_cost_ids:
            order_qty = line.balance_qty or line.quantity
            if (
                    order_qty > 0
                    and line.quantity != line.po_qty
                    and line.product_id
                    and line.product_id.detailed_type != 'service'
            ):
                has_any = True
                orderline.append((0, 0, {
                    'code': line.code,
                    'product_id': line.product_id.id,
                    'qty': order_qty,
                    'units': line.uom_id.id,
                    'price_unit': line.unit_price,
                    'material_cost_id': line.id,
                }))
        for line in active_id.item_ids:
            order_qty = line.balance_qty or line.quantity
            if order_qty > 0 and line.quantity != line.po_qty:
                has_any = True
                orderline.append((0, 0, {
                    'code': line.code,
                    'name': line.description,
                    'qty': order_qty,
                    'units': line.uom_id.id,
                    'price_unit': line.unit_price,
                    'item_id': line.id,
                }))
        print(orderline,"orderline")

        if not has_any:
            raise ValidationError(_("No Material Cost or Item lines available to create RFQ."))

        return {
            'name': 'Create RFQ',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'kg.create.rfq.wizard',
            'target': 'new',
            'context': {
                'default_estimation_id': active_id.id,
                'default_division_id': active_id.division_id.id if active_id.division_id else False,
                'default_order_line_ids': orderline,
            }
        }


class KGSaleCRMLeafInherit(models.Model):
    _inherit = "crm.lead"

    division_id = fields.Many2one("kg.divisions", string="Division")
    type_id = fields.Selection([('local', 'Local'), ('meast', 'Middle east'), ('international', 'International'),
                                ('sisconcern', 'Sister Concern'), ('subcontracting', 'Subcontracting')],
                               default='sisconcern', string="Type", related='partner_id.po_type', store=True)

    def open_rfq_wizard(self):
        return {
            'name': 'Create RFQ',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'kg.create.rfq.wizard',
            'target': 'new',
            'context': {
                'default_opportunity_id': self.id,
                'default_division_id': self.division_id.id if self.division_id else False,
            }
        }

# class MailComposerInherit(models.TransientModel):
#     _inherit = 'mail.compose.message'
#
#     def action_send_mail(self, auto_commit=False):
#         result = super(MailComposerInherit, self)._action_send_mail(auto_commit=auto_commit)
#         if result:
#             if self.env.context.get('proforma') and self.model == 'sale.order':
#                 res_ids = self.res_ids
#                 if isinstance(res_ids, str):
#                     try:
#                         res_ids = ast.literal_eval(res_ids)
#                     except Exception:
#                         res_ids = []
#
#                 if res_ids:
#                     record = self.env['sale.order'].browse(res_ids[0])
#                     if result and record:
#                         record.proforma_invoice_no = self.env['ir.sequence'].next_by_code('proforma.inv')
#
#         return result
