from ast import literal_eval

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    state = fields.Selection([('new', 'New'), ('approval', 'Approved')],
                             string='Status', default='new')

    po_type = fields.Selection([('local', 'Local'), ('meast', 'Middle east'), ('international', 'International'),
                                ('sisconcern', 'Sister Concern'), ('subcontracting', 'Subcontracting')],
                               default='sisconcern', string="Type")
    is_approved =fields.Boolean(string="Is Approved")
    is_coa_installed =fields.Boolean()
    hide_peppol_fields =fields.Boolean()
    vendor_group_id = fields.Many2one('vendor.group',string = "Vendor Group")
    property_payment_term_ids = fields.Many2many('account.payment.term','rec_id',
                                               string='Customer Payment Terms',
                                               help="This payment term will be used instead of the default one for sales orders and customer invoices")

    max_payment_days = fields.Integer(
        compute="_compute_max_payment_days",
    )

    @api.depends('property_payment_term_id')
    def _compute_max_payment_days(self):
        for rec in self:
            if rec.property_payment_term_id:
                # Ensure that we map the 'days' field correctly
                days_list = rec.property_payment_term_id.mapped('days')  # mapped to 'days' field
                rec.max_payment_days = max(days_list or [0])  # Safeguard for empty list
            else:
                rec.max_payment_days = 0

    @api.onchange('property_payment_term_id')
    def _onchange_property_payment_term_id(self):
        if not self.property_payment_term_id:
            return

        max_days = max(
            self.property_payment_term_id.mapped('days') or [0]
        )

        self.property_payment_term_ids = self.property_payment_term_ids.filtered(
            lambda t: max(t.mapped('days') or [0]) <= max_days
        )

    def action_approval(self):
        if self.supplier_rank > 0:
            vendor_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_purchase.vendor_approval_ids', '[]')
            vendor_approve_users = eval(vendor_approve_users) if isinstance(eval(vendor_approve_users), list) else []
            if self.env.user.id not in vendor_approve_users:
                raise UserError(_("You have no access to approve"))
            note = f'The user {self.env.user.name} has approved the request for {self.name}.'
            self.message_post(body=note)
            self._process_activities('kg_purchase.customer_approval_notification')
        if self.customer_rank > 0:
            customer_approve_users = self.env['ir.config_parameter'].sudo().get_param(
                'kg_voyage_marine_sale.customer_ids', '[]')
            customer_approve_users = eval(customer_approve_users) if isinstance(eval(customer_approve_users),
                                                                                list) else []
            if self.env.user.id not in customer_approve_users:
                raise UserError(_("You have no access to approve"))
            note = f'The user {self.env.user.name} has approved the request for {self.name}.'
            self.message_post(body=note)
            self._process_activities('kg_purchase.customer_approval_notification')
        self.is_approved = True
        self.write({'state': 'approval'})

    def _process_activities(self, activity_xml_id):
        """Helper function to process activities."""
        approval_activity = self.env.ref(activity_xml_id)
        activity = self.activity_ids.filtered(
            lambda l: l.activity_type_id == approval_activity)
        if activity:
            activity.action_done()
        activities_to_unlink = self.activity_ids.filtered(
            lambda l: l.activity_type_id == approval_activity and l.user_id != self.env.user)

        for activity_to_unlink in activities_to_unlink:
            activity_to_unlink.unlink()

    @api.model
    def create(self, vals):
        vendor = super(Partner, self).create(vals)
        if vals.get('supplier_rank', 0) > 0:
            vendor.send_vendor_approval_notification()
        if vals.get('customer_rank', 0) > 0:
          # default_payment_term = self.env['account.payment.term'].search([('is_default_payment_term','=',True)])
          # vendor.property_payment_term_id = default_payment_term.id
          vendor.send_customer_approval_notification()
        return vendor

    def send_vendor_approval_notification(self):
        pm_users = []
        vendor_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_purchase.vendor_approval_ids', False)
        if not vendor_approve_users or vendor_approve_users == '[]':
            raise ValidationError(_("Please Select Approval Users in Configuration"))
        if vendor_approve_users:
            pm_approve_users = vendor_approve_users.replace('[', '').replace(']', '').replace('"', '').replace("'","").strip()
            pm_approve_users_id = [int(uid) for uid in pm_approve_users.split(',') if uid]
            users = self.env['res.users'].browse(pm_approve_users_id)

            for user in users:
                email_subject = f"Vendor Approval Request for {self.name}"
                email_body = f"""
                        <p>Dear {user.name},</p>
                        <p>A new vendor, <strong>{self.name}</strong>, has been created by {self.env.user.name}. Please verify and approve the vendor.</p>
                        <p>Thank you.</p>
                    """
                mail_values = {
                    'subject': email_subject,
                    'body_html': email_body,
                    'email_to': user.email,
                    'author_id': self.env.user.partner_id.id,
                    'model': 'res.partner',
                    'res_id': self.id,
                }

                mail = self.env['mail.mail'].sudo().create(mail_values)
                mail.sudo().send()
            if literal_eval(vendor_approve_users):
                for i in literal_eval(vendor_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        pm_users.append(users)

                for user in pm_users:
                    self.activity_schedule('kg_purchase.purchase_manager_approval_notification',
                                           user_id=user.id,
                                           note=f' The User {self.env.user.name} request approve to the vendor {self.name}. Please Verify and approve.')

    def send_customer_approval_notification(self):
        cus_users = []
        customer_approve_users = self.env['ir.config_parameter'].sudo().get_param(
            'kg_voyage_marine_sale.customer_ids', False)
        if not customer_approve_users or customer_approve_users == '[]':
            raise ValidationError(_("Please Select Approval Users in Configuration"))
        if customer_approve_users:
            cus_approve_users = customer_approve_users.replace('[', '').replace(']', '').replace('"', '').replace("'","").strip()
            cm_approve_users_id = [int(uid) for uid in cus_approve_users.split(',') if uid]
            users = self.env['res.users'].browse(cm_approve_users_id)

            for user in users:
                email_subject = f"Customer Approval Request for {self.name}"
                email_body = f"""
                        <p>Dear {user.name},</p>
                        <p>A new Customer, <strong>{self.name}</strong>, has been created by {self.env.user.name}. Please verify and approve the customer.</p>
                        <p>Thank you.</p>
                    """
                mail_values = {
                    'subject': email_subject,
                    'body_html': email_body,
                    'email_to': user.email,
                    'author_id': self.env.user.partner_id.id,
                    'model': 'res.partner',
                    'res_id': self.id,
                }

                mail = self.env['mail.mail'].sudo().create(mail_values)
                mail.sudo().send()
            if literal_eval(customer_approve_users):
                for i in literal_eval(customer_approve_users):
                    users = self.env['res.users'].browse(i)
                    if users:
                        cus_users.append(users)

                for user in cus_users:
                    self.activity_schedule('kg_purchase.purchase_manager_approval_notification',
                                           user_id=user.id,
                                           note=f' The User {self.env.user.name} request approve to the vendor {self.name}. Please Verify and approve.')


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"
    _description = "Payment Terms"

    is_default_payment_term = fields.Boolean(string="IS Default Payment Term", default=False,copy=False)

    _sql_constraints = [
        ('unique_is_default_payment_term', 'unique(is_default_payment_term)', 'Only one record can set to True (100% Advance Terms).')
    ]