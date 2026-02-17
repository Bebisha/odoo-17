# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class PurchaseRequisitions(models.Model):
    _name = "purchase.requisitions"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence'
    _order = 'sequence desc'
    _description = "Purchase Requisitions"

    def _get_buyer_domain(self):
        purchase_manager = self.env.ref('purchase.group_purchase_manager').users
        purchase_user = self.env.ref('purchase.group_purchase_user').users
        user_ids = []
        for usr in purchase_user:
            if usr.id not in purchase_manager.ids:
                user_ids.append(usr.id)
        return [('id', 'in', user_ids)]

    # APPROVAL

    check_po = fields.Boolean(compute="compute_check_po")
    is_batch_req = fields.Boolean(string="Is Batch Requisition", default=False)
    purchase_user_id = fields.Many2one('res.users', string='Purchase Representative', domain=_get_buyer_domain)

    @api.depends('requisition_line_ids')
    def compute_check_po(self):
        self.check_po = False
        if self.requisition_line_ids and sum(self.requisition_line_ids.mapped('demand_qty')) <= sum(
                self.requisition_line_ids.mapped('purchase_quantity')):
            self.check_po = True

    # PO Created
    # def approve(self):
    #     """ Conditions check while approving """
    #     for rec in self.requisition_line_ids:
    #         income_account = rec.product_id.property_account_income_id
    #         budget_lines = self.env['account.budget.post'].search([('company_id', '=', self.company_id.id)])
    #         if income_account in budget_lines.mapped('account_ids'):
    #             line = budget_lines.mapped('id')
    #             budget = self.env['crossovered.budget.lines'].search([('general_budget_id', '=', line),
    #                                                                   ('crossovered_budget_state', '=', 'confirm'),
    #                                                                   ('company_id', '=', self.company_id.id)])
    #             Total = self.amount_total + budget.practical_amount
    #             if budget.planned_amount < Total:
    #                 group_mail = []
    #                 pur_group = self.env.ref('purchase.group_purchase_manager').mapped('users')
    #                 account_manager = self.env.ref('account.group_account_manager').mapped('users')
    #                 for usr in pur_group:
    #                     if usr.email:
    #                         group_mail.append(usr.email)
    #                 for usr in account_manager:
    #                     if usr.email:
    #                         group_mail.append(usr.email)
    #                 users_mail = ",".join(group_mail)
    #                 email_values = {
    #                     'email_to': users_mail,
    #                     'email_from': self.env.user.email_formatted,
    #                 }
    #                 mail_template = self.env.ref('bi_material_purchase_requisitions.budget_email_template_id')
    #                 mail = mail_template.send_mail(self.id, email_values=email_values, force_send=True)
    #                 raise ValidationError(_('Budget is Exceeded the Limit'))
    #             self.write({'state': 'in_progress'})
    #         else:
    #             self.write({'state': 'in_progress'})
    #             res = super(PurchaseRequisitions, self).approve()
    #     else:
    #         self.write({'state': 'in_progress'})
    #         res = super(PurchaseRequisitions, self).approve()
    #     return res

    @api.onchange('employee_id')
    def get_emp_data(self):
        if self.employee_id:
            self.destination_location_id = self.employee_id.destination_location_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['sequence'] = self.env['ir.sequence'].next_by_code('purchase.requisitions') or '/'
        return super(PurchaseRequisitions, self).create(vals_list)

    @api.model
    def default_get(self, flds):
        result = super(PurchaseRequisitions, self).default_get(flds)
        result['requisition_date'] = datetime.now()
        return result

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '{} ({})'.format(rec.sequence, rec.requisition_date)))
        return res

    # Vendor RFQ
    def send_rfq(self):
        """ Function for send RFQ to Vendors for created PO """
        for rec in self:
            purchase_orders = self.env['purchase.order'].search(
                [('pr_requisition_id', '=', rec.id),
                 ('state', '=', 'draft')])
            for order in purchase_orders:
                order.action_rfq_send()

    def action_cancel(self):
        for requisition in self:
            pur_requisition_ids = self.env['purchase.order'].search([('origin', '=', requisition.sequence)])
            if pur_requisition_ids:
                for p_req in pur_requisition_ids:
                    p_req.button_cancel()
                    p_req.unlink()
            requisition.write({'state': 'cancel'})
        if self.requisition_id:
            body = _('Purchase Request %s canceled', self.sequence)
            self.requisition_id.message_post(body=body)
            # self.requisition_id.button_cancel()
        self.write({'state': 'cancel'})

    def action_reject(self):
        for requisition in self:
            requisition.write({
                'state': 'cancel',
                'rejected_date': datetime.now(),
                'rejected_by': self.env.user.id
            })

    def action_reset_draft(self):
        for requisition in self:
            # req = requisition.with_context(active_id=requisition.id, active_model=requisition._name)
            # approval_vals = req.approval_id._get_initial_approval_structure()
            # req._update_approval_state('request', approval_vals)
            requisition.write({
                'state': 'new',
                'completion_date': False
            })

    def _get_internal_picking_count(self):
        for picking in self:
            picking.internal_picking_count = 0

    def internal_picking_button(self):
        self.ensure_one()

    def _get_purchase_order_count(self):
        for rec in self:
            po_ids = self.env['purchase.order'].search([]).filtered(
                lambda x: rec.id in x.pr_requisition_ids.ids)
            rec.purchase_order_count = len(po_ids)

    def purchase_order_button(self):
        self.ensure_one()
        po_ids = self.env['purchase.order'].search([]).filtered(
            lambda x: x.pr_requisition_id.id == self.id or self.id in x.pr_requisition_ids.ids)
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', po_ids.ids)],
        }

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.company.id
        types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return types[:1]

    def _get_employeed(self):
        user = self.env['res.users'].browse(self.env.uid)
        employee_id = False
        if user:
            employee_id = user.employee_id or False
        return employee_id

    sequence = fields.Char(string='Sequence', readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string="Employee", default=_get_employeed)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id')
    requisition_responsible_id = fields.Many2one('res.users', string="Requisition Responsible")
    requisition_date = fields.Date(string="Requisition Date", required=True)
    received_date = fields.Date(string="Received Date", readonly=True)
    requisition_deadline_date = fields.Date(string="Requisition Deadline")
    state = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancel')], string='Stage', default="new")
    requisition_line_ids = fields.One2many('requisition.line', 'pr_requisition_id', string="Requisition Line ID")
    confirmed_by_id = fields.Many2one('res.users', string="Confirmed By", copy=False)
    department_manager_id = fields.Many2one('res.users', string="Department Manager", copy=False)
    approved_by_id = fields.Many2one('res.users', string="Approved By", copy=False)
    rejected_by = fields.Many2one('res.users', string="Rejected By", copy=False)
    confirmed_date = fields.Date(string="Confirmed Date", readonly=True, copy=False)
    department_approval_date = fields.Date(string="Department Approval Date", readonly=True, copy=False)
    approved_date = fields.Date(string="Approved Date", readonly=True, copy=False)
    rejected_date = fields.Date(string="Rejected Date", readonly=True, copy=False)
    reason_for_requisition = fields.Html(string="Reason For Requisition")
    source_location_id = fields.Many2one('stock.location', string="Source Location")
    destination_location_id = fields.Many2one('stock.location', string="Destination Location")
    purchase_order_count = fields.Integer('Purchase Order', compute='_get_purchase_order_count')
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    picking_type_id = fields.Many2one('stock.picking.type', 'Purchase Operation Type', required=True,
                                      default=lambda self: self._default_picking_type())
    use_manual_locations = fields.Boolean(string="Select Manual Locations")
    # Faliwa Dev
    # #############################################
    amount_total = fields.Float(compute='_computed_amount_all')
    requisition_action = fields.Selection([
        ('purchase_order', 'Purchase Order'),
        ('po_and_picking', 'Both PO and Picking'),
        ('internal_picking', 'Internal Picking')],
        string="Requisition Action", default='purchase_order')
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    department_res_id = fields.Many2one('hr.department', string="Department Responsible")
    depart_responsible_id = fields.Many2one('hr.employee', string="Responsible")
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
    requisition_id = fields.Many2one('material.purchase.requisition', string="Material Requisition", copy=False)
    mr_ids = fields.Many2many('material.purchase.requisition', string="Material Requisitions", compute="compute_mr_ids")
    mr_count = fields.Integer(compute="compute_mr_count")
    remarks = fields.Char("Remarks")
    completion_date = fields.Datetime('Completion Date', copy=False, readonly=True)

    def action_done(self):
        print("iiiiiiiiiiii")
        for requisition in self:
            requisition.write({'state': 'done', 'completion_date': datetime.now()
                               })

    @api.depends('mr_ids')
    def compute_mr_count(self):
        self.mr_count = len(self.mr_ids)

    @api.depends('requisition_id', 'requisition_line_ids')
    def compute_mr_ids(self):
        for rec in self:
            req_ids = rec.requisition_line_ids.mapped('requisition_id').ids
            req_id = rec.requisition_id.ids
            mr_ids = req_ids + req_id
            rec.mr_ids = [(6, 0, mr_ids)]

    def action_view_mr(self):
        return {
            'name': 'Material Requisition',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'material.purchase.requisition',
            'domain': [('id', 'in', self.mr_ids.ids)],
        }

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

    @api.onchange('depart_responsible_id', 'employee_id')
    def onchange_depart_responsible_id(self):
        if self.depart_responsible_id:
            self.department_res_id = self.depart_responsible_id.department_id
        if self.employee_id:
            self.department_id = self.employee_id.department_id

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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    po_requisition_id = fields.Many2one('purchase.requisition', string="Purchase Requisition")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    pr_requisition_id = fields.Many2one('purchase.requisitions', string="Purchase Requisition")
    pr_requisition_ids = fields.Many2many('purchase.requisitions', string="Purchase Requisitions")
    project_id = fields.Many2one('project.project', 'Project')
    delivery_date = fields.Date('Delivery Date')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    req_line_id = fields.Char('Req Line ID')
    req_line_ids = fields.Many2many('requisition.line')
