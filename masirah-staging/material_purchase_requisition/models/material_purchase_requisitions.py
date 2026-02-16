

# -*- coding: utf-8 -*-
from ast import literal_eval
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class MaterialPurchaseRequisition(models.Model):
    _name = "material.purchase.requisition"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence'
    _order = 'sequence desc'
    _description = "Material Purchase Requisition"

    sequence = fields.Char(string='Sequence', readonly=True, copy=False, default="New")
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  default=lambda self: self.env.user.employee_id.id,
                                  required=True)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    readonly=True)
    requisition_responsible_id = fields.Many2one('res.users', string="Requisition Responsible")
    requisition_date = fields.Date(string="Requisition Date", required=True)
    petty_cash_based = fields.Boolean(string='Petty Cash Based', default=False)
    is_transport = fields.Boolean(string="Is Transport")
    received_date = fields.Date(string="Received Date", readonly=True)
    requisition_deadline_date = fields.Date(string="Requisition Deadline")
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('material_issue', 'Material Issued'),
        ('pr', 'Purchase Requisition'),
        ('reject', 'Reject'),
        ('cancel', 'Cancel')], string='Stage', default="new")
    # is_material_issued = fields.Boolean(string='Material Issue', compute="_compute_is_material_issued")
    is_pr = fields.Boolean(string="Created Pr", default=False)
    requisition_line_ids = fields.One2many('requisition.line', 'requisition_id', string="Requisition Line ID",
                                           copy=True)
    confirmed_by_id = fields.Many2one('res.users', string="Confirmed By", copy=False)
    department_manager_id = fields.Many2one('res.users', string="Department Manager", copy=False)
    approved_by_id = fields.Many2one('res.users', string="Approved By", copy=False)
    rejected_by = fields.Many2one('res.users', string="Rejected By", copy=False)
    confirmed_date = fields.Date(string="Confirmed Date", readonly=True, copy=False)
    department_approval_date = fields.Date(string="Department Approval Date", readonly=True, copy=False)
    approved_date = fields.Date(string="Approved Date", readonly=True, copy=False)
    rejected_date = fields.Date(string="Rejected Date", readonly=True, copy=False)
    reason_for_requisition = fields.Html(string="Reason For Requisition", required=False)
    source_location_id = fields.Many2one('stock.location', string="Source Location")
    destination_location_id = fields.Many2one('stock.location', string="Destination Location")
    internal_picking_count = fields.Integer('Internal Picking Count', compute='_get_picking_count')
    delivery_picking_count = fields.Integer('Internal Picking Count', compute='_get_picking_count')
    purchase_requisition_count = fields.Integer('Purchase Requisitions', compute='_get_purchase_requisition_count')
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    use_manual_locations = fields.Boolean(string="Select Manual Locations")
    capital_purchase = fields.Boolean(string="Capital Purchase")
    vehicle_no = fields.Char("Vehicle no")
    amount_total = fields.Float(compute='_computed_amount_all')
    requisition_action = fields.Selection([
        ('purchase_order', 'Purchase Order'),
        ('po_and_picking', 'Both PO and Picking'),
        ('internal_picking', 'Internal Picking')],
        string="Requisition Action", default='purchase_order')

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    department_res_id = fields.Many2one('hr.department', string="Department Request", required=True)
    depart_responsible_id = fields.Many2one('hr.employee', string="Responsible", related='department_res_id.manager_id',
                                            readonly=False)
    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit",
                                        related='depart_responsible_id.operating_unit_id', store=True)
    is_head = fields.Boolean(string="Head", related='operating_unit_id.is_head', store=True)
    phase_sjr = fields.Selection([
        ('exp', 'Exploration'),
        ('cons', 'Construction'),
        ('mo', 'Mining & Operations')], string="Phase", default='exp')
    current_operating_unit_id = fields.Many2one(
        "operating.unit",
        string="Current Operating Unit",
        default=lambda self: self._default_operating_unit(),
    )

    # APPROVAL

    requisition_id = fields.Many2one('purchase.requisitions', copy=False)
    is_employee_required = fields.Boolean('Employee')
    picking_ids = fields.Many2many('stock.picking', string='Pickings', copy=False)
    picking_count = fields.Integer(string='Transfers', compute='_compute_picking_ids', copy=False)
    pr_ids = fields.Many2many('purchase.requisitions', string='Purchase Requisitions', copy=False)
    pr_count = fields.Integer(string='PRs', compute='_compute_pr_ids', copy=False)
    is_stock = fields.Boolean('Stock Bool', compute='_compute_stock_bool')
    is_issued = fields.Boolean('Is Issued', compute='_compute_is_issued')
    complaints_id = fields.Many2one('property.maintenance', readonly=True)
    comments = fields.Text(string="Comments")
    remarks = fields.Char('Remarks')
    completion_date = fields.Datetime('Completion Date', copy=False, readonly=True)
    issue_against = fields.Selection([('location', 'Location'), ('employee', 'Employee')],
                                     string="Material Issued against", default='location')
    issue_location = fields.Many2one('stock.location', string='Issue Location', store=True)

    is_request = fields.Boolean(default=False)
    is_wait_dm_approve = fields.Boolean(default=False)
    is_dm_approve = fields.Boolean(default=False)

    @api.onchange('issue_against')
    def _onchange_issue_against(self):
        if self.issue_against == 'location':
            self.issue_location = False
        if self.issue_against == 'employee':
            if not self.employee_id.destination_location_id:
                raise UserError('Location for issue not set in employee')
            self.issue_location = self.employee_id.destination_location_id.id

    @api.depends('requisition_line_ids', 'requisition_line_ids.issued_qty')
    def _compute_is_issued(self):
        for rec in self:
            rec.is_issued = False
            if any(x.qty - x.issued_qty > 0 for x in rec.requisition_line_ids):
                rec.is_issued = True

    @api.depends('pr_ids')
    def _compute_pr_ids(self):
        for order in self:
            order.pr_count = len(order.pr_ids)

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.picking_count = len(order.picking_ids)

    def action_view_pr(self):
        return {
            'name': 'Purchase Request',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.requisitions',
            'domain': [('id', 'in', self.pr_ids.ids)],
        }

    @api.onchange('employee_id')
    def get_emp_data(self):
        if self.employee_id:
            self.destination_location_id = self.employee_id.destination_location_id.id

    def kg_request(self):
        dm_users = []

        dm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.department_manager_ids', False)

        if not dm_approve_users or dm_approve_users == '[]':
            raise ValidationError(_("Please Select Department Manager in Configuration"))

        if literal_eval(dm_approve_users):
            for i in literal_eval(dm_approve_users):
                users = self.env['res.users'].browse(i)
                if users:
                    dm_users.append(users)

            for user in dm_users:
                self.activity_schedule('material_purchase_requisition.department_manager_approval_notification',
                                       user_id=user.id,
                                       note=f' The User {self.env.user.name} request the Department Manager to approve the Material Requisition {self.sequence}. Please Verify and approve.')

        self.is_wait_dm_approve = True

    def kg_dm_approve(self):
        dm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.department_manager_ids', False)

        if self.env.user.id not in literal_eval(dm_approve_users):
            raise UserError(_("You have no access to approve"))

        else:
            department_manager_notification_activity = self.env.ref(
                'material_purchase_requisition.department_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == department_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == department_manager_notification_activity)
            activity_2.action_done()

            dm_users = []

            if literal_eval(dm_approve_users):
                for i in literal_eval(dm_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        dm_users.append(users)

                for user in dm_users:
                    self.activity_schedule('material_purchase_requisition.material_requisition_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved the Department manager approval of the Material Requisition {self.sequence}.')

            material_req_notification_activity = self.env.ref(
                'material_purchase_requisition.material_requisition_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == material_req_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == material_req_notification_activity)
            activity_2.action_done()

        self.is_dm_approve = True
        self.action_confirm()

    def kg_reject(self):
        dm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.department_manager_ids', False)

        if self.env.user.id not in literal_eval(dm_approve_users):
            raise UserError(_("You have no access to reject"))

        else:
            self.activity_schedule('material_purchase_requisition.reject_material_requisition_notification',
                                   user_id=self.create_uid.id,
                                   note=f' The user {self.env.user.name}  has rejected the approval of the Material Requisition {self.sequence}.')

            reject_material_requisition_notification_activity = self.env.ref(
                'material_purchase_requisition.reject_material_requisition_notification')
            activity = self.activity_ids.filtered(
                lambda l: l.activity_type_id == reject_material_requisition_notification_activity)
            activity.action_done()

            department_manager_notification_activity = self.env.ref(
                'material_purchase_requisition.department_manager_approval_notification')
            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == department_manager_notification_activity)
            activity_1.unlink()

            self.action_reject()


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['sequence'] = self.env['ir.sequence'].next_by_code('material.purchase.requisition') or '/'
            vals['is_request'] = True
        return super(MaterialPurchaseRequisition, self).create(vals_list)

    @api.model
    def default_get(self, flds):
        result = super(MaterialPurchaseRequisition, self).default_get(flds)
        result['requisition_date'] = datetime.now()
        return result

    def _prepare_pr_line_vals(self):
        lines = []
        for line in self.requisition_line_ids:
            vals = {
                'description': line.description,
                'product_id': line.product_id.id,
                'qty': line.pr_quantity,
                'uom_id': line.uom_id.id,
            }
            lines.append((0, 0, vals))
        return lines

    def action_create_pr(self):
        if all(line.pr_requisition_id.state != 'cancel' and line.pr_requisition_id for line in
               self.requisition_line_ids):
            raise UserError(_("Purchase requisition has already been created against all lines!"))

        if any(line.pr_quantity for line in self.requisition_line_ids):
            pr_values = {
                'employee_id': self.employee_id.id,
                'department_id': self.department_id.id,
                'department_res_id': self.department_res_id.id,
                'requisition_responsible_id': self.requisition_responsible_id.id,
                'requisition_date': self.requisition_date,
                'requisition_deadline_date': self.requisition_deadline_date,
                'received_date': self.received_date,
                'state': 'new',
                'company_id': self.company_id.id,
                'currency_id': self.currency_id.id,
                'requisition_id': self.id,
                'reason_for_requisition': self.reason_for_requisition,
            }
            pr_id = self.env['purchase.requisitions'].create(pr_values)
            for line in self.requisition_line_ids:
                if line.pr_requisition_id.state == 'cancel' or not line.pr_requisition_id:
                    if line.pr_quantity:
                        line.pr_requisition_id = pr_id.id
                        line.demand_qty = line.pr_quantity
                        self.pr_ids |= pr_id

    def create_material_issue(self):
        """ Helps to create material issue for mR"""
        stock_picking_obj = self.env['stock.picking']
        stock_picking_type_obj = self.env['stock.picking.type']
        for requisition in self:
            # if not requisition.is_done:
            #     raise UserError(_("Please get the Material Request Approved before Confirmation"))

            picking_type_id = stock_picking_type_obj.search(
                [('code', '=', 'internal'), ('company_id', '=', requisition.company_id.id or False),
                 ('is_material_issue', '=', True)],
                order="id desc", limit=1)
            if not picking_type_id:
                raise ValidationError(
                    _('Create a Operation Type for Material Issue .'))

            pic_line_val = [(5, 0, 0)]
            for line in requisition.requisition_line_ids:
                # pro_sml = requisition.picking_ids.filtered(lambda x: x.state == 'waiting').mapped('move_ids_without_package').filtered(lambda x: x.mr_line_id.id == line.id)
                if not requisition.issue_location:
                    raise UserError("Configure Material Issue destination location!")
                if not requisition.department_res_id.destination_location_id:
                    raise UserError("Configure the Destination location within the department request!")
                available_qty = line.product_id.with_context(
                    {'location': requisition.department_res_id.destination_location_id.id}).qty_available
                qty = line.balance_qty
                if qty > available_qty:
                    qty = available_qty

                if qty > 0:
                    pic_line_val.append((0, 0, {
                        # 'partner_id': line.vendor_id.id,
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom_qty': qty,
                        'product_uom': line.uom_id.id,
                        'location_id': requisition.department_res_id.destination_location_id.id or picking_type_id.default_location_dest_id.id,
                        'location_dest_id': requisition.issue_location.id or picking_type_id.default_location_src_id.id,
                        'origin': requisition.sequence,
                        'mr_line_id': line.id,
                        # 'user_id': requisition.id,
                    }))

            if pic_line_val != [(5, 0, 0)]:
                draft_picking = requisition.picking_ids.filtered(lambda x: x.state == 'draft')
                if draft_picking:
                    draft_picking.write({'move_ids_without_package': pic_line_val})
                else:
                    val = {
                        # 'partner_id': line.vendor_id.id,
                        'picking_type_id': picking_type_id.id,
                        'company_id': requisition.env.user.company_id.id,
                        'requisition_picking_id': requisition.id,
                        'location_id': requisition.department_res_id.destination_location_id.id or picking_type_id.default_location_dest_id.id,
                        'location_dest_id': requisition.issue_location.id or picking_type_id.default_location_src_id.id,
                        'origin': requisition.sequence,
                        # 'vehicle_id': requisition.vehicle_id.id,
                        'move_ids_without_package': pic_line_val
                    }
                    stock_picking = stock_picking_obj.sudo().create(val)
                    requisition.picking_ids |= stock_picking
            else:
                raise UserError("Products are not available for issue!")

    def action_confirm(self):
        for requisition in self:
            requisition.write({'state': 'in_progress'})

    def action_done(self):
        for requisition in self:
            if not requisition.is_dm_approve:
                raise UserError(_("Please get the Material Request Approved before Confirmation"))
            requisition.write({'state': 'done', 'completion_date': datetime.now()
                               })

    def button_cancel(self):
        for requisition in self:
            batch_pr_lines = self.env['purchase.requisitions'].search([('is_batch_req', '=', True)]).mapped(
                'requisition_line_ids').filtered(lambda x: x.requisition_id.id == self.id)
            if batch_pr_lines:
                for line in batch_pr_lines:
                    if line.pr_requisition_id.state == 'new':
                        line.pr_requisition_id = False
                    else:
                        raise UserError(
                            _("You cannot cancel this material request, the batch request has already been created and processed"))
            requisition.write({'state': 'cancel'})

    def action_cancel(self):
        for requisition in self:
            batch_pr_lines = self.env['purchase.requisitions'].search([('is_batch_req', '=', True)]).mapped(
                'requisition_line_ids').filtered(lambda x: x.requisition_id.id == self.id)
            if batch_pr_lines:
                for line in batch_pr_lines:
                    if line.pr_requisition_id.state == 'new':
                        line.pr_requisition_id = False
                    else:
                        raise UserError(
                            _("You cannot cancel this material request, the batch request has already been created and processed"))
            picking_requisition_ids = self.env['stock.picking'].search([('origin', '=', requisition.sequence)])
            if picking_requisition_ids:
                for req in picking_requisition_ids:
                    req.action_cancel()
                    req.unlink()
            pur_requisition_ids = self.pr_ids
            if pur_requisition_ids:
                for p_req in pur_requisition_ids:
                    p_req.action_cancel()
                    p_req.unlink()
            requisition.write({'state': 'cancel'})

    def action_reject(self):
        for requisition in self:
            picking_requisition_ids = self.env['stock.picking'].search([('origin', '=', requisition.sequence)])
            if picking_requisition_ids:
                for req in picking_requisition_ids:
                    req.action_cancel()
                    req.unlink()
            pur_requisition_ids = self.env['purchase.order'].search([('origin', '=', requisition.sequence)])
            if pur_requisition_ids:
                for p_req in pur_requisition_ids:
                    p_req.button_cancel()
                pur_requisition_ids.unlink()
            requisition.write({
                'state': 'reject',
                'rejected_date': datetime.now(),
                'rejected_by': self.env.user.id
            })

    def action_reset_draft(self):
        for requisition in self:
            req = requisition.with_context(active_id=requisition.id, active_model=requisition._name)
            # approval_vals = req.approval_id._get_initial_approval_structure()
            # req._update_approval_state('request', approval_vals)
            picking_requisition_ids = self.env['stock.picking'].search(
                [('requisition_picking_id', '=', requisition.id)])
            if picking_requisition_ids:
                picking_requisition_ids.action_cancel()
                # req.unlink()
            pur_requisition_ids = self.env['purchase.order'].search([('origin', '=', requisition.sequence)])
            if pur_requisition_ids:
                for p_req in pur_requisition_ids:
                    p_req.button_cancel()
                pur_requisition_ids.unlink()
            requisition.write({
                'state': 'new',
                'completion_date': False,
                'is_request': True,
                'is_wait_dm_approve': False,
                'is_dm_approve': False,
            })

    def _get_picking_count(self):
        for picking in self:
            internal_picking_ids = self.env['stock.picking'].search(
                [('requisition_picking_id', '=', picking.id)]).filtered(lambda p: p.picking_type_id.code == 'internal')
            outgoing_picking_ids = self.env['stock.picking'].search(
                [('requisition_picking_id', '=', picking.id)]).filtered(lambda p: p.picking_type_id.code == 'outgoing')
            picking.internal_picking_count = len(internal_picking_ids)
            picking.delivery_picking_count = len(outgoing_picking_ids)

    def _get_purchase_requisition_count(self):
        for rec in self:
            pr_ids = self.env['purchase.requisitions'].search([('requisition_id', '=', rec.id)])
            batch_pr_ids = self.requisition_line_ids.mapped('pr_requisition_id')
            rec.purchase_requisition_count = len(batch_pr_ids)

    def delivery_pickings_button(self):
        outgoing_picking_ids = self.env['stock.picking'].search([('requisition_picking_id', '=', self.id)]).filtered(
            lambda p: p.picking_type_id.code == 'outgoing')

        return {
            'name': 'Delivery Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', outgoing_picking_ids.ids)],
        }

    def get_department(self):
        user = self.env['res.users'].browse(self.env.uid)
        department = False
        if user:
            department = user.employee_id.department_id or False
        return department

    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        return action

    @api.model
    def operating_unit_default_get(self, uid2=False):
        if not uid2:
            uid2 = self._uid
        user = self.env["res.users"].browse(uid2)
        return user.default_operating_unit_id

    @api.model
    def _default_operating_unit(self):
        return self.operating_unit_default_get()

    @api.model
    def _default_operating_units(self):
        return self._default_operating_unit()

    @api.onchange('requisition_action')
    def onchange_requisition_action(self):
        if self.requisition_action:
            for line in self.requisition_line_ids:
                line.requisition_action = self.requisition_action

    @api.depends('requisition_line_ids.total_price')
    def _computed_amount_all(self):
        for requisition in self:
            total = 0
            if requisition.requisition_line_ids:
                total += sum(line.total_price for line in requisition.requisition_line_ids)
            requisition.amount_total = total

    @api.onchange('currency_id')
    def _onchange_price_requisition(self):
        for line in self.requisition_line_ids:
            line._onchange_price()
            line._onchange_total()

    # def approve(self):
    #     res = super(MaterialPurchaseRequisition, self).approve()
    #     self = self.with_context(active_id=self.id, active_model=self._name)
    #     approval_vals = self.approvals_json
    #     if not approval_vals.get('next_approval'):
    #         self.action_confirm()
    #     return res

    @api.depends('requisition_line_ids.product_id.qty_available')
    def _compute_stock_bool(self):
        for rec in self:
            rec.is_stock = True
            for requisition_line in rec.requisition_line_ids:
                product = requisition_line.product_id
                if product and product.qty_available > 0:
                    rec.is_stock = False


# #############################################
class RequisitionLine(models.Model):
    _name = "requisition.line"
    _description = "Requisition Line"
    _rec_name = 'description'

    @api.model
    def create(self, vals):
        if vals.get('requisition_id'):
            existing_line = self.search([('product_id', '=', vals.get('product_id')),
                                         ('requisition_id', '=', vals.get('requisition_id')),
                                         ('uom_id', '=', vals.get('uom_id'))])
            if existing_line and vals.get('qty'):
                existing_line.qty += vals.get('qty')
                return existing_line
            else:
                res = super(RequisitionLine, self).create(vals)
                return res
        else:
            res = super(RequisitionLine, self).create(vals)
            return res

    @api.onchange('product_id', 'qty')
    def onchange_product_id(self):
        res = {}
        if not self.product_id:
            return res
        self.uom_id = self.product_id.uom_id.id
        self.description = self.product_id.name
        product_onhand = self.env['product.product'].search([('id', '=', self.product_id.id)]).qty_available
        if self.qty > product_onhand:
            self.is_not_available = True

    @api.depends('qty', 'issued_qty', 'purchase_quantity')
    def _compute_pr_quantity(self):
        for rec in self:
            rec.pr_quantity = rec.qty - rec.issued_qty - rec.purchase_quantity

    product_id = fields.Many2one('product.product', string="Product", domain="[('type','not in',['service'])]")
    description = fields.Text(string="Description", required=True)
    is_not_available = fields.Boolean("Is available", default=False)
    qty = fields.Float(string="Qty", default=1.0, required=True)
    demand_qty = fields.Float(string="Quantity", default=1.0)
    uom_id = fields.Many2one('uom.uom', string="Unit Of Measure")
    requisition_id = fields.Many2one('material.purchase.requisition', string="MR", copy=False)
    pr_requisition_id = fields.Many2one('purchase.requisitions', string="PR", copy=False)
    po_ids = fields.Many2one('purchase.order', string="Purchase Order", copy=False)
    req_line_id = fields.Char('Req Line ID', store=True)
    remarks = fields.Char('Remarks')
    pr_remarks = fields.Char('Remarks')
    requisition_action = fields.Selection([
        ('purchase_order', 'Purchase Order'),
        ('po_and_picking', 'Both PO and Picking'),
        ('internal_picking', 'Internal Picking')], string="Requisition Action", default='purchase_order')
    vendor_id = fields.Many2one('res.partner', string="Vendors", domain=[('supplier_rank', '>', 0)])
    price_unit = fields.Monetary("Unit Price")
    total_price = fields.Monetary("Total")
    currency_id = fields.Many2one('res.currency', string='Currency', related='requisition_id.currency_id')
    issued_qty = fields.Float(string="Issued Quantity", compute='get_qty')
    pr_quantity = fields.Float(string="PR Qty", help="Purchase Requisition Quantity", compute="_compute_pr_quantity")
    po_quantity = fields.Float(string="PO Qty", help="Quantity to purchase")
    purchase_quantity = fields.Float(string="Purchased Qty", compute='get_purchase_qty', default=0)
    balance_qty = fields.Float(string="Balance Qty", compute='get_balance_issue_qty', default=0)

    @api.onchange('po_quantity')
    def onchange_po_quantity(self):
        if self.demand_qty < self.po_quantity:
            raise ValidationError(_('PO quantity should not be greater than requested quantity !'))

    @api.depends('issued_qty', 'qty')
    def get_balance_issue_qty(self):
        for rec in self:
            demand_qty = 0
            stock_moves = self.env['stock.move'].sudo().search(
                [('mr_line_id', '=', rec.id), ('state', 'not in', ['done', 'cancel'])])
            if stock_moves:
                demand_qty = sum(stock_moves.mapped('product_uom_qty'))
            rec.balance_qty = rec.qty - (rec.issued_qty + demand_qty)

    @api.depends('requisition_id.picking_ids')
    def get_qty(self):
        for rec in self:
            requisition_id = rec.requisition_id
            issued_line_ids = requisition_id.mapped('picking_ids.move_ids_without_package').filtered(
                lambda l: l.picking_id.state == 'done' and l.mr_line_id.id == rec.id)
            issued_qty = 0.00
            for line in issued_line_ids:
                if line.product_uom.id != rec.uom_id.id:
                    issued_qty += line.product_uom._compute_quantity(line.quantity_done, rec.product_uom_id,
                                                                     rounding_method='HALF-UP')
                else:
                    issued_qty += line.quantity
            rec.issued_qty = issued_qty

    @api.depends('requisition_id.pr_ids')
    def get_purchase_qty(self):
        for rec in self:
            purchase = self.env['purchase.order'].search([]).filtered(
                lambda x: rec.pr_requisition_id.id in x.pr_requisition_ids.ids)
            order_lines = purchase.order_line.filtered(lambda x: x.product_id.id == rec.product_id.id)
            total_received = sum(order_lines.mapped('qty_received'))
            if order_lines.mapped('req_line_ids') or order_lines.mapped('req_line_id'):
                rec.purchase_quantity = rec.qty
            else:
                rec.purchase_quantity = total_received

    def _prepare_stock_moves(self):
        values = []
        for line in self:
            if not line.issued_qty or line.qty > line.issued_qty:
                values.append((0, 0, line._prepare_stock_move_values(line)))
        return values

    def _prepare_stock_move_values(self, line):
        self.ensure_one()
        requisition_id = line.requisition_id
        picking_type_id = self.env['stock.picking.type'].search(
            [('code', '=', 'internal'), ('company_id', '=', self.requisition_id.company_id.id or False),
             ('is_material_issue', '=', True)],
            order="id desc", limit=1)
        if not picking_type_id:
            raise ValidationError(
                _('Create a Operation Type for Material Issue .'))
        vals = {
            'name': line.product_id.name,
            'mr_line_id': line.id,
            'product_id': line.product_id.id,
            'product_uom': line.uom_id and line.uom_id.id or line.product_id.uom_id.id,
            'date': requisition_id.requisition_date,
            'date_expected': requisition_id.requisition_date,
            'location_id': picking_type_id.default_location_src_id.id,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'state': 'draft',
            'company_id': line.requisition_id.company_id.id,
            'picking_type_id': picking_type_id.id,
            'product_uom_qty': line.qty - line.issued_qty,
            'quantity_done': line.qty - line.issued_qty,
            'reserved_availability': line.qty - line.issued_qty,
            'origin': requisition_id.sequence,
        }
        return vals

    @api.onchange('qty', 'price_unit')
    def _onchange_total(self):
        if self.product_id and self.qty:
            self.total_price = self.price_unit * self.qty

    def action_view_stock(self):
        view = self.env.ref('material_purchase_requisition.view_product_stock_location')
        return {
            'name': _('Location Wise Product Stock'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.loc.stock',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
            },
        }


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    requisition_picking_id = fields.Many2one('material.purchase.requisition', string="Purchase Requisition")

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.picking_type_id.is_material_issue:
            for move in self.move_ids:
                done_qty = move.quantity
                requisition_line = move.requisition_line_id
                if requisition_line:
                    requisition_line.issued_qty = done_qty
                    requisition_line.demand_qty -= done_qty
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    requisition_line_id = fields.Many2one('requisition.line', string="Material Requisition Line")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    requisition_po_id = fields.Many2one('material.purchase.requisition', string="Purchase Requisition")
    pr_requisition_ids = fields.Many2many('purchase.requisitions', 'rel_pr_po', string="Purchase Requisition")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    destination_location_id = fields.Many2one('stock.location', string="Destination Location")


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    destination_location_id = fields.Many2one('stock.location', string="Destination Location",
                                              related="employee_id.destination_location_id")
    group_id = fields.Many2one('res.groups', string="Destination Location", related="employee_id.group_id")
    operating_unit_id = fields.Many2one('operating.unit', string="Destination Location",
                                        related="employee_id.operating_unit_id")


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    destination_location_id = fields.Many2one('stock.location', string="Destination Location")

