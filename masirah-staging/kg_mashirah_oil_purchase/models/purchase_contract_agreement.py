from odoo import models, fields, api, _
from datetime import date
from ast import literal_eval

from odoo.exceptions import ValidationError, UserError


class PurchaseContractAgreement(models.Model):
    _name = "purchase.contract.agreement"
    _description = "Purchase Contract Agreement"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Contract Reference")
    vendor_id = fields.Many2one("res.partner", string="Vendor")
    date_from = fields.Datetime(string="Date From", default=date.today())
    date_to = fields.Datetime(string="Date To", default=date.today())
    vendor_ref = fields.Char(string="Vendor Reference")
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id, string="Currency")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'Ongoing'),
        ('close', 'Close'),
        ('cancel', 'Cancel')], default='draft', tracking=True)
    purchase_contract_ids = fields.One2many('purchase.contract.agreement.line', 'purchase_contract_id',
                                            string='Purchase Contract Lines')
    company_id = fields.Many2one('res.company', readonly=True, default=lambda self: self.env.company)
    purchase_ids = fields.Many2many("purchase.order", string="Purchase Reference", copy=False)
    po_count = fields.Integer(string="PO Count", compute="compute_po_count")
    is_receipt = fields.Boolean(string="Is Receipt", compute="compute_is_receipt")
    is_create_rfq = fields.Boolean(string='Button Clicked', invisible=True, default=False, copy=False)
    is_dm_approve = fields.Boolean(string="Is Department Manager Approve", default=False, copy=False)
    department_manager = fields.Many2one('res.users')

    rfq_created_pc_lines = fields.Many2many('purchase.contract.agreement.line', 'pc_rel',
                                            string='RFQ Created PC Lines')

    def kg_dm_approve(self):
        dm_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_purchase.department_manager_ids', False)

        if self.env.user.id not in literal_eval(dm_approve_users):
            raise UserError(_("You have no access to approve"))

        else:
            department_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_purchase.department_manager_approval_notification')

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
                    self.activity_schedule('kg_mashirah_oil_purchase.department_manager_approval_notification',
                                           user_id=user.id,
                                           note=f' The user {self.env.user.name} has approved for creating RFQ {self.name}.')

            department_manager_notification_activity = self.env.ref(
                'kg_mashirah_oil_purchase.department_manager_approval_notification')

            activity_1 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == department_manager_notification_activity)
            not_current_user_confirm = activity_1.filtered(lambda l: l.user_id != self.env.user)

            for ccc in not_current_user_confirm:
                ccc.unlink()

            activity_2 = self.activity_ids.filtered(
                lambda l: l.activity_type_id == department_manager_notification_activity)
            activity_2.action_done()

            self.is_dm_approve = True
            self.is_create_rfq = True

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('kg.purchase.contract.seq')
        return super(PurchaseContractAgreement, self).create(vals)

    @api.onchange('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_("The start date must be less than the end date"))

    def action_confirm(self):
        if not self.purchase_contract_ids:
            raise ValidationError("Empty Purchase Contract Lines: Add items to continue!!!!!")

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
                self.activity_schedule('kg_mashirah_oil_purchase.department_manager_approval_notification',
                                       user_id=user.id,
                                       note=f' The User {self.env.user.name} request the Department Manager to approve the Purchase Contract {self.name}. Please Verify and approve.')
        self.write({
            'state': 'ongoing'
        })

    def create_rfq(self):
        if self.purchase_contract_ids:
            orderline = []
            today_date = date.today()
            contract_line_ids = self.purchase_contract_ids.filtered(
                lambda x: x.start_date and x.end_date and x.start_date <= today_date and x.end_date >= today_date)
            if contract_line_ids:
                for line in contract_line_ids:
                    line_vals = (0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.description,
                        'product_qty': 1,
                        'price_unit': line.unit_price,
                        'product_uom': line.uom_id.id,
                    })
                    orderline.append(line_vals)
                vals = {
                    'partner_id': self.vendor_id.id,
                    'order_line': orderline,
                    'partner_ref': self.vendor_ref,
                    'currency_id': self.currency_id.id,
                    'purchase_contract_id': self.id,
                }
                po_id = self.env['purchase.order'].create(vals)
                self.purchase_ids = [(4, po_id.id)]
                for crtl in contract_line_ids:
                    self.rfq_created_pc_lines = [(4, crtl.id)]
                self.is_create_rfq = True
                self.is_dm_approve = True
                return {
                    'name': 'Purchase Order',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'purchase.order',
                    'res_id': po_id.id,
                }
            else:
                raise ValidationError("You cannot create an RFQ since no purchase contract exists for today!!")

    def action_close(self):
        self.write({
            'state': 'close'
        })

    def action_cancel(self):

        self.write({
            'state': 'cancel'
        })

        if self.purchase_ids:
            for line in self.purchase_ids:
                line.state = 'cancel'

    @api.depends('purchase_ids')
    def compute_po_count(self):
        for rec in self:
            if rec.purchase_ids:
                rec.po_count = len(rec.purchase_ids)
            else:
                rec.po_count = 0

    @api.depends('purchase_ids')
    def compute_is_receipt(self):
        for rec in self:
            if rec.purchase_ids:
                if any(li.picking_ids for li in self.purchase_ids):
                    rec.is_receipt = True
                else:
                    rec.is_receipt = False
            else:
                rec.is_receipt = False

    def action_view_purchase_order(self):
        return {
            'name': 'Purchase Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.purchase_ids.ids)],
            'target': 'current'
        }

    def extend(self):
        extend_lines = []
        view_id = self.env.ref('kg_mashirah_oil_purchase.purchase_contract_extend_wizard_view').id
        product_id = self.purchase_contract_ids.mapped('product_id')
        for prod in product_id:
            contract_line_ids = self.purchase_contract_ids.filtered(lambda x: x.product_id.id == prod.id)
            if contract_line_ids:
                price_unit = contract_line_ids[-1].unit_price
                description = contract_line_ids[-1].description
            else:
                price_unit = 0.00
                description = False
            line_vals = (0, 0, {
                'product_id': prod.id,
                'unit_price': price_unit,
                'description': description,
                'uom_id': prod.uom_id.id,
            })
            extend_lines.append(line_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Contract Extension'),
            'res_model': 'purchase.contract.extend.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': {'default_purchase_contract_id': self.id,
                        'default_purchase_contract_extend_line_ids': extend_lines}
        }

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You cannot delete a record which is not in draft state'))
        return super(PurchaseContractAgreement, self).unlink()

    def button_draft(self):
        if not self.purchase_ids:
            self.state = 'draft'
            self.is_create_rfq = False
            self.is_dm_approve = False
        else:
            self.state = 'ongoing'
            self.purchase_ids = self.purchase_ids


class PurchaseContractAgreementLine(models.Model):
    _name = "purchase.contract.agreement.line"
    _description = "Purchase Contract Agreement Line"

    name = fields.Char(string="Name")
    purchase_contract_id = fields.Many2one('purchase.contract.agreement', string="Purchase Contract")
    product_id = fields.Many2one("product.product", string="Product")
    description = fields.Char(string="Description")
    uom_id = fields.Many2one("uom.uom", string="UOM")
    unit_price = fields.Float(string="Unit Price")
    company_id = fields.Many2one('res.company', readonly=True, default=lambda self: self.env.company)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.model
    def create(self, vals):
        res = super(PurchaseContractAgreementLine, self).create(vals)
        if not res.start_date and res.purchase_contract_id:
            res.start_date = res.purchase_contract_id.date_from.date()
        if not res.end_date and res.purchase_contract_id:
            res.end_date = res.purchase_contract_id.date_to.date()
        return res

    def get_description(self, product_id):
        name = product_id.display_name
        if product_id.description_purchase:
            name += '\n' + product_id.description_purchase
        return name

    @api.onchange('product_id')
    def get_line_values(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_id.id
                rec.unit_price = rec.product_id.standard_price
                rec.description = rec.get_description(rec.product_id)

    @api.onchange('start_date', 'end_date')
    def check_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')
