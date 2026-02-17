# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import fields, models, _, api
from odoo.exceptions import UserError
from ast import literal_eval


class KgMaterialRequest(models.Model):
    _name = "kg.material.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Kg Material Request"
    _order = 'name desc'

    name = fields.Char(string='Reference', required=True,
                       readonly=True, default=lambda self: _('New'))

    partner_id = fields.Many2one('res.partner','Customer',required=True, domain="[('is_inv_customer', '=', True)]")
    request_date = fields.Date(string="Request Date", default=lambda self: fields.Date.context_today(self))
    requested_by = fields.Many2one('res.partner',string="Requested By")
    requested_by_id = fields.Many2one('res.users',string="Requested By",default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.company)
    type = fields.Selection([('sale', 'Create Sale Order'), ('internal', "Create Transfer")], string='Request Type',default='sale', readonly=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('request', 'Requested'),
            ('approve', 'Approved'),
            ('reject', 'Rejected'),
            ('sale', 'Sale Order'),
            ('internal', 'Transfer'),
            ('cancel', 'Cancelled'),
        ],
        string='States',
        tracking=True,
        default='draft',
    )

    approved_by = fields.Many2one('res.users',string="Approved By", readonly=True)
    approve_date = fields.Date(string="Approved Date", readonly=True)
    notes = fields.Html('Notes')

    rejected_by = fields.Many2one('res.users',string="Rejected By", readonly=True)
    reject_date = fields.Date(string="Reject Date", readonly=True)
    reject_reason = fields.Text(string="Reject Reason", readonly=True)

    material_line_ids =  fields.One2many('material.request.line','material_id',string="material line ids")
    is_request_for_approval = fields.Boolean(default=True)

    internal_transfer_ids = fields.One2many(
        'stock.picking', 'origin', string='Internal Transfers', relation='internal_stock_rel',
        domain=[('picking_type_id.code', '=', 'internal')]
    )
    sale_order_ids = fields.Many2many('sale.order', string="Sale Orders")
    stock_ids = fields.Many2many('stock.picking', string="Transfer", relation='stock_rel',compute='compute_transfer')

    transfer_count = fields.Integer(string="Transfer Count" ,compute='_compute_transfer_count')
    sale_count = fields.Integer(string="Transfer Count" , compute='_compute_sale_count')

    def _compute_sale_count(self):
        for rec in self:
            if rec.sale_order_ids:
                rec.sale_count = len(rec.sale_order_ids)
            else:
                self.sale_count = 0

    def _compute_transfer_count(self):
        for rec in self:
            if rec.stock_ids:
                rec.transfer_count = len(rec.stock_ids)
            else:
                self.transfer_count = 0

    def compute_transfer(self):
        for rec in self:
            rec.stock_ids=self.env['stock.picking'].search([('request_id','=',self.id)]).ids



    def action_request_for_approval_button(self):
        for rec in self:
            if not rec.material_line_ids:
                raise UserError(_("Please select the products."))

            rec.state='request'
            rec.send_mail()

    def action_cancel_button(self):
        self.state = 'cancel'

    def action_reset_to_draft_button(self):
        for rec in self:
            if rec.type == 'sale':
                confirmed_sale_orders = any(so.state not in ['draft', 'cancel'] for so in rec.sale_order_ids)
                if confirmed_sale_orders:
                    raise UserError(_("Cannot reset to draft. The associated sale orders are confirmed."))
                rec.sale_order_ids.filtered(lambda x: x.state == 'draft').action_cancel()
                rec.state = 'draft'
            if rec.type == 'internal':
                stock_orders = any(so.state not in ['draft', 'cancel'] for so in rec.stock_ids)
                if stock_orders:
                    raise UserError(_("Cannot reset to draft. The associated Transfers are confirmed."))
                rec.stock_ids.filtered(lambda x: x.state == 'draft').action_cancel()
                rec.state = 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('kg.material.request.sequence') or 'New'
        return super(KgMaterialRequest, self).create(vals_list)


    def action_approve_button(self):
        for rec in self:
            rec.state = 'approve'
            rec.approved_by = self.env.user.id
            rec.approve_date = fields.Date.today()
            rec.send_approval_notification()
            if rec.type == 'internal':
                rec.action_internal_transfer_button()
            else:
                rec.action_create_sale_order_button()

    def action_reject_button(self):
        return {
            'name': _('Reject Reason'),
            'type': 'ir.actions.act_window',
            'res_model': 'rejects.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_material_id': self.id,
            }
        }


    def action_create_sale_order_button(self):
        """ Create Sale Orders for each unique Customer in the Material Request """
        if not self.material_line_ids:
            raise UserError(_('No materials found to create a Sale Order.'))
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'date_order': fields.Datetime.now(),
            'company_id': self.company_id.id,
            'request_id':self.id,
            'order_line': [(0, 0, {
                'product_id': line.product_id.id,
                'name': line.description,
                'tax_id': False,
                'product_uom_qty': line.quantity,
                'price_unit': line.unit_price,
                'product_uom': line.uom_id.id
            }) for line in self.material_line_ids]
        })
        self.sale_order_ids = [(6, 0, sale_order.ids)]
        self.state = 'sale'


    def action_internal_transfer_button(self):
        stock_location_from = self.company_id.source_id
        stock_location = self.company_id.destination_id
        operation_from_type = self.company_id.picking_type_id
        if not stock_location:
            raise UserError('Please configure destination location')

        if not operation_from_type:
            raise UserError('Please configure picking type')

        picking = self.env['stock.picking'].sudo().create({
            'partner_id': self.partner_id.id,
            'picking_type_id': operation_from_type.id,
            'location_id': stock_location_from.id,
            'location_dest_id': stock_location.id,
            'date': self.request_date or fields.Date.today(),
            'origin': self.name,
            'request_id': self.id,
        })

        moves = [(0, 0, {
            'partner_id': self.partner_id.id,
            'picking_id': picking.id,
            'product_uom_qty': line.quantity,
            'name': line.product_id.name,
            'product_id': line.product_id.id,
            'product_uom': line.uom_id.id,
            'location_id': stock_location_from.id,
            'location_dest_id': stock_location.id,
        }) for line in self.material_line_ids]

        picking.write({'move_ids': moves})
        # self.stock_ids = [(6, 0, picking.ids)]
        self.state = 'internal'

    def action_view_transfer(self):
        self.ensure_one()
        return {
            'name': 'Transfer',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('request_id','=',self.id)],
        }

    def action_view_quotations(self):
        self.ensure_one()
        if len(self.sale_order_ids) == 1:
            return {
                'name': 'Sale Order',
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': self.sale_order_ids.id,
                'view_mode': 'form',
            }
        else:
            return {
                'name': 'Sale Order',
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.sale_order_ids.ids)],
            }

    def send_mail(self):
        """Send email notification to approvers when a material request is submitted for approval"""
        approval_group = self.env.ref('kg_material_request.material_request_group_approval')
        approval_users = approval_group.users.filtered(lambda u: u.email)

        if not approval_users:
            raise UserError(_("No approvers found with email addresses!"))

        recipient_emails = [user.email for user in approval_users]

        subject = _("Material Request Approval Required")
        body = _(
            """
            <p>Dear,</p>
            <p>New Material Request has been submitted by <strong>%s</strong> and requires your approval.</p>
            <p><strong>Reference:</strong> %s</p>
            <p><strong>Requested Date:</strong> %s</p>
            <p><strong>Requested By:</strong> %s</p>
            <p>Please review the request and take necessary action.</p>
            <p><a href="%s">Click here to view the request</a></p>
            <p>Thank you.</p>
            """
        ) % (
                   self.requested_by_id.name,
                   self.name,
                   self.request_date,
                   self.requested_by_id.name,
                   self.get_material_request_url(),
               )

        outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        email_from = outgoing_mail_server.sudo().smtp_user if outgoing_mail_server else self.env.user.email

        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': ', '.join(recipient_emails),
            'email_from': email_from,
        }

        self.env['mail.mail'].sudo().create(mail_values).send()

    def get_material_request_url(self):
        """Generate the URL for approvers to view the material request"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web#id={self.id}&view_type=form&model={self._name}"

    def send_approval_notification(self):
        """Send email notification to the requester upon approval"""
        if not self.requested_by_id.email:
            raise UserError(_("The requester does not have an email address!"))

        subject = _("Your Material Request Has Been Approved")
        body = _(
            """
            <p>Dear %s,</p>
            <p>Your material request <strong>%s</strong> has been approved by <strong>%s</strong>.</p>
            <p><strong>Approved Date:</strong> %s</p>
            <p>You can view the approved request here:</p>
            <p><a href="%s">View MR</a></p>
            <p>Thank you.</p>
            """
        ) % (
                   self.requested_by_id.name,
                   self.name,
                   self.approved_by.name,
                   self.approve_date,
                   self.get_material_request_url(),
               )

        outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        email_from = outgoing_mail_server.sudo().smtp_user if outgoing_mail_server else self.env.user.email

        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': self.requested_by_id.email,
            'email_from': email_from,
        }

        self.env['mail.mail'].sudo().create(mail_values).send()

        approval_group = self.env.ref('kg_material_request.material_request_group_manager')
        approval_users = approval_group.users.filtered(lambda u: u.email)

        if not approval_users:
            raise UserError(_("No material request managers found with email addresses!"))

        recipient_emails = [user.email for user in approval_users]

        subject = _("Material Request Has Been Approved")
        body = _(
            """
            <p>Dear ,</p>
            <p>Material request <strong>%s</strong> has been approved by <strong>%s</strong>.</p>
            <p><strong>Approved Date:</strong> %s</p>
            <p>You can view the approved request here:</p>
            <p><a href="%s">View MR</a></p>
            <p>Please review and do the needful</p>
            <p>Thank you.</p>
            """
        ) % (
                   self.name,
                   self.approved_by.name,
                   self.approve_date,
                   self.get_material_request_url(),
               )

        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': ', '.join(recipient_emails),
            'email_from': email_from,
        }

        self.env['mail.mail'].sudo().create(mail_values).send()


    def get_material_values(self):
        request_data = []
        is_admin = self.env.user.has_group('base.group_system')

        if not is_admin:
            requests = self.env['kg.material.request'].sudo().search([('state', 'in', ['request'])])
        else:
            requests = self.env['kg.material.request'].sudo().search([('state', 'in', ['request'])])
        for req in requests:
            state = dict(req._fields['state'].selection).get(req.state,
                                                               '') if req else ''
            type = dict(req._fields['type'].selection).get(req.type,
                                                               '') if req else ''
            formatted_date = req.create_date.strftime('%d/%m/%Y') if req.create_date else ''

            request_data.append({
                'id': req.id,
                'name': req.name,
                'partner_id': req.partner_id.name,
                'company': req.company_id.name,
                'company_id': req.company_id.id,
                'request_date': formatted_date,
                'request_by_id': req.requested_by_id.id,
                'request_by_name': req.requested_by_id.name,
                'state': state,
                'type': type,
            #     'leaves': [leave.id for leave in leaves if leave.employee_id.id == employee.id],
            })

        company_data = []
        # companies = self.env['res.company'].sudo().search([])
        companies = self.env.user.sudo().company_ids

        for company in companies:
            company_data.append({
                'id': company.id,
                'name': company.name,
                'country_code': company.country_id.code if company.country_id else '',
            })

        return {
            'requests': request_data,
            'companies': company_data,
        }


class MaterialRequestLine(models.Model):
    _name = "material.request.line"
    _description = "Material Request Line"

    product_id = fields.Many2one('product.product' ,string="Product", required=True,domain=[('detailed_type', '=', 'product'), ('qty_available', '>', 1)])
    # , ('qty_available', '>', 1)
    default_code = fields.Char(string="Part code", related='product_id.default_code')
    description = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity", required=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='product_id.uom_id')
    unit_price = fields.Float(string="Unit Price")
    reason = fields.Text(string="Reason/Ticket", required=True)
    subtotal = fields.Monetary(string="Subtotal", compute='_compute_subtotal')
    material_id = fields.Many2one('kg.material.request', string="Material id")
    currency_id = fields.Many2one(related="company_id.currency_id", string='Currency', readonly=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    received_qty = fields.Float(string="Received Qty", compute='_compute_received_qty')

    def _compute_received_qty(self):
        for line in self:
            line.received_qty=False
            received_qty=False
            if line.material_id.type=='internal':
                for picking in line.material_id.stock_ids:
                    for move in picking.move_ids_without_package:
                        if (move.product_id == line.product_id):

                            received_qty += move.quantity
            else:
                for sale_order in line.material_id.sale_order_ids:
                    for order_line in sale_order.order_line:
                        if (order_line.product_id == line.product_id):
                            received_qty += order_line.qty_delivered

            line.received_qty = received_qty

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            line.description = line.product_id.name
            line.unit_price = line.product_id.standard_price
