# -*- coding: utf-8 -*-
import ast
from base64 import encodebytes
from datetime import datetime
from io import BytesIO
import xlsxwriter
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    label_invoice_line = fields.Char(string='Label', compute='_compute_label_invoice_line', store=True)

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Distribution',
                                          compute='_compute_analytic_distribution')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'), ('approval_requested', 'Approval Requested'), ('approved', 'Approved'),
            ('posted', 'Posted'),
            ('rejected', 'Rejected'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )
    currency_omr = fields.Many2one('res.currency', string='Currency OMR', copy=False, compute='compute_currency_omr')
    reason_for_reject = fields.Char(string="Reason for Reject", copy=False, tracking=True)

    need_invoice_approve = fields.Boolean(default=False, copy=False, string="Invoice Approve",
                                          related="company_id.need_invoice_approve")

    need_bill_approve = fields.Boolean(default=False, copy=False, string="Bill Approve",
                                       related="company_id.need_bill_approve")

    is_forwarding_approval = fields.Boolean(default=False, copy=False, string="Is Forwarding Approval")
    first_approve_user_id = fields.Many2one("res.users", string="First Approver", copy=False)
    first_final_approve_user_id = fields.Many2one("res.users", string="First Final Approver", copy=False)

    communication = fields.Char(string="Communication", compute="compute_communication")

    approval_id = fields.Many2one("approval.request", string="Approvals", copy=False)
    final_approval_id = fields.Many2one("approval.request", string="Final Approvals", copy=False)

    bank_ids = fields.Many2many("res.partner.bank", string="Banks", compute="compute_bank_ids")
    correspondent_bank_ids = fields.Many2many("res.partner.bank", string="Correspondent Banks",
                                              compute="compute_correspondent_bank_ids")

    kg_analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account")

    kg_invoice_no = fields.Char(string="Invoice Number", copy=False)

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    @api.model_create_multi
    def create(self, vals):
        for i in vals:
            if i['move_type'] == 'out_invoice':
                i['kg_invoice_no'] = self.env['ir.sequence'].next_by_code('kg.invoice.no.seq')
        return super(AccountMove, self).create(vals)

    @api.onchange('kg_analytic_account_id')
    def _onchange_kg_analytic_account_id(self):
        for line in self.invoice_line_ids:
            if self.kg_analytic_account_id:
                line.analytic_distribution = {str(self.kg_analytic_account_id.id): 100}
            else:
                line.analytic_distribution = {}

    def compute_bank_ids(self):
        for rec in self:
            rec.bank_ids = False
            if rec.company_id and rec.company_id.bank_ids and rec.currency_id:
                bank_ids = self.company_id.bank_ids.filtered(
                    lambda x: x.currency_id.id == rec.currency_id.id and not x.is_correspondent_bank)
                if bank_ids:
                    rec.bank_ids = bank_ids.ids

    def compute_correspondent_bank_ids(self):
        for rec in self:
            rec.correspondent_bank_ids = False
            if rec.company_id and rec.company_id.bank_ids and rec.currency_id:
                correspondent_bank_ids = self.company_id.bank_ids.filtered(
                    lambda x: x.currency_id.id == rec.currency_id.id and x.is_correspondent_bank)
                if correspondent_bank_ids:
                    rec.correspondent_bank_ids = correspondent_bank_ids.ids

    def compute_communication(self):
        for rec in self:
            rec.communication = False
            aml_name = [name for name in rec.line_ids.mapped('name') if name]
            if aml_name:
                i = aml_name[0]
                if i and ']' in i:
                    try:
                        end = i.index(']') + 1
                        name = f"{ast.literal_eval(i[:end])} {i[end:].strip()}"
                        if len(aml_name) > 1:
                            name += f", {aml_name[1]}"
                        rec.communication = f"{rec.ref} - {name}" if rec.ref else name
                    except (ValueError, SyntaxError):
                        rec.communication = f"{rec.ref} - {i}" if rec.ref else i
                else:
                    rec.communication = f"{rec.ref} - {i}" if rec.ref else i

    default_inv_approve_users_ids = fields.Many2many("res.users", string="Invoice Approvers", copy=False,
                                                     compute="compute_inv_approve_users")

    default_bill_approve_users_ids = fields.Many2many("res.users", 'bill_approve_rel', string="Bill Approvers",
                                                      copy=False, compute="compute_bill_approve_users")

    default_inv_final_approve_users_ids = fields.Many2many("res.users", 'inv_final_approve_rel',
                                                           string="Invoice Approvers", copy=False,
                                                           compute="compute_inv_final_approve_users")

    default_bill_final_approve_users_ids = fields.Many2many("res.users", 'bill_final_approve_rel',
                                                            string="Bill Approvers",
                                                            copy=False, compute="compute_bill_final_approve_users")

    inv_approve_user_id = fields.Many2one("res.users", string="Invoice Approver", copy=False, tracking=True)
    bill_approve_user_id = fields.Many2one("res.users", string="Bill Approver", copy=False, tracking=True)

    inv_final_approve_user_id = fields.Many2one("res.users", string="Invoice Final Approver", copy=False, tracking=True)
    bill_final_approve_user_id = fields.Many2one("res.users", string="Bill Final Approver", copy=False, tracking=True)

    approve_forwarded = fields.Boolean(default=False, copy=False, string="Approve Forwarded")

    need_final_approve = fields.Boolean(default=False, string="Need Approve Limit", compute="compute_final_approve")
    invoice_limit = fields.Monetary(string="Invoice Limit", compute="compute_invoice_limit",
                                    currency_field="company_currency_id")
    bill_limit = fields.Monetary(string="Bill Limit", compute="compute_bill_limit",
                                 currency_field="company_currency_id")
    waiting_final_approve = fields.Boolean(default=False, copy=False, string="Waiting Final Approve")

    ##################################################################################################################################

    @api.depends('create_uid')
    def compute_inv_approve_users(self):
        for rec in self:
            rec.default_inv_approve_users_ids = False
            approver_ids = self.env['ir.config_parameter'].sudo().get_param(
                'kg_raw_fisheries_accounting.invoice_approvers_ids', '[]')
            if approver_ids:
                approver_ids = ast.literal_eval(approver_ids)
                users = self.env['res.users'].browse(approver_ids)
                if users:
                    rec.default_inv_approve_users_ids = [(6, 0, users.ids)]

    @api.depends('create_uid')
    def compute_bill_approve_users(self):
        for rec in self:
            rec.default_bill_approve_users_ids = False
            approver_ids = self.env['ir.config_parameter'].sudo().get_param(
                'kg_raw_fisheries_accounting.bill_approvers_ids', '[]')
            if approver_ids:
                approver_ids = ast.literal_eval(approver_ids)
                users = self.env['res.users'].browse(approver_ids)
                if users:
                    rec.default_bill_approve_users_ids = [(6, 0, users.ids)]

    @api.depends('create_uid')
    def compute_inv_final_approve_users(self):
        for rec in self:
            rec.default_inv_final_approve_users_ids = False
            approver_ids = self.env['ir.config_parameter'].sudo().get_param(
                'kg_raw_fisheries_accounting.invoice_final_approvers_ids', '[]')
            if approver_ids:
                approver_ids = ast.literal_eval(approver_ids)
                users = self.env['res.users'].browse(approver_ids)
                if users:
                    rec.default_inv_final_approve_users_ids = [(6, 0, users.ids)]

    @api.depends('create_uid')
    def compute_bill_final_approve_users(self):
        for rec in self:
            rec.default_bill_final_approve_users_ids = False
            approver_ids = self.env['ir.config_parameter'].sudo().get_param(
                'kg_raw_fisheries_accounting.bill_final_approvers_ids', '[]')
            if approver_ids:
                approver_ids = ast.literal_eval(approver_ids)
                users = self.env['res.users'].browse(approver_ids)
                if users:
                    rec.default_bill_final_approve_users_ids = [(6, 0, users.ids)]

    ################################################################################################################################################

    def compute_invoice_limit(self):
        for rec in self:
            rec.invoice_limit = 0.00
            invoice_limit = self.env['ir.config_parameter'].sudo().get_param(
                'kg_raw_fisheries_accounting.invoice_limit')
            if invoice_limit:
                rec.invoice_limit = invoice_limit

    def compute_bill_limit(self):
        for rec in self:
            rec.bill_limit = 0.00
            bill_limit = self.env['ir.config_parameter'].sudo().get_param('kg_raw_fisheries_accounting.bill_limit')
            if bill_limit:
                rec.bill_limit = bill_limit

    ########################################################################################################################

    def compute_final_approve(self):
        for rec in self:
            rec.need_final_approve = False
            amount_total_signed = abs(rec.amount_total_signed) if rec.amount_total_signed else 0.00
            if rec.move_type == 'out_invoice' and rec.amount_total_signed and rec.invoice_limit and amount_total_signed > rec.invoice_limit:
                rec.need_final_approve = True
            elif rec.move_type == 'in_invoice' and rec.amount_total_signed and rec.bill_limit and amount_total_signed > rec.bill_limit:
                rec.need_final_approve = True
            else:
                rec.need_final_approve = False

    @api.depends('restrict_mode_hash_table', 'state')
    def _compute_show_reset_to_draft_button(self):
        for move in self:
            move.show_reset_to_draft_button = (
                    not move.restrict_mode_hash_table and (
                    move.state == 'cancel' or (
                    move.state == 'posted' and not move.need_cancel_request)) or move.state == 'rejected'
            )

    def button_draft(self):
        if any(move.state not in ('cancel', 'posted', 'rejected') for move in self):
            raise UserError(_("Only posted/cancelled/rejected journal entries can be reset to draft."))
        if any(move.need_cancel_request for move in self):
            raise UserError(
                _("You can't reset to draft those journal entries. You need to request a cancellation instead."))

        self._check_draftable()
        self.mapped('line_ids.analytic_line_ids').unlink()
        self.mapped('line_ids').remove_move_reconcile()
        self.state = 'draft'
        self.is_forwarding_approval = False
        self.first_approve_user_id = False
        self.first_final_approve_user_id = False
        self.approve_forwarded = False
        self.waiting_final_approve = False

    ########################################################################################################################

    @api.onchange('bill_approve_user_id')
    def forwarding_bill_approve(self):
        if self.bill_approve_user_id and self.first_approve_user_id:
            group = self.env.ref('kg_raw_fisheries_accounting.invoice_bill_forward_group', raise_if_not_found=False)
            if self.first_approve_user_id != self.env.user and not (group and self.env.user in group.users):
                raise ValidationError("You do not have access to change the approved user")
            if self.first_approve_user_id != self.bill_approve_user_id:
                self.is_forwarding_approval = True
                self.approve_forwarded = False
            else:
                self.is_forwarding_approval = False

    @api.onchange('inv_approve_user_id')
    def forwarding_invoice_approve(self):
        if self.inv_approve_user_id and self.first_approve_user_id:
            group = self.env.ref('kg_raw_fisheries_accounting.invoice_bill_forward_group', raise_if_not_found=False)
            if self.first_approve_user_id != self.env.user or not (group and self.env.user in group.users):
                raise ValidationError("You do not have access to change the approved user")
            if self.first_approve_user_id != self.inv_approve_user_id:
                self.is_forwarding_approval = True
                self.approve_forwarded = False
            else:
                self.is_forwarding_approval = False

    @api.onchange('bill_final_approve_user_id')
    def forwarding_bill_final_approve(self):
        if self.bill_final_approve_user_id and self.first_final_approve_user_id:
            group = self.env.ref('kg_raw_fisheries_accounting.invoice_bill_forward_group', raise_if_not_found=False)
            if self.first_final_approve_user_id != self.env.user or not (group and self.env.user in group.users):
                raise ValidationError("You do not have access to change the approved user")
            if self.first_final_approve_user_id != self.bill_final_approve_user_id:
                self.is_forwarding_approval = True
                self.approve_forwarded = False
            else:
                self.is_forwarding_approval = False

    @api.onchange('inv_final_approve_user_id')
    def forwarding_invoice_final_approve(self):
        if self.inv_final_approve_user_id and self.first_final_approve_user_id:
            group = self.env.ref('kg_raw_fisheries_accounting.invoice_bill_forward_group', raise_if_not_found=False)
            if self.first_final_approve_user_id != self.env.user or not (group and self.env.user in group.users):
                raise ValidationError("You do not have access to change the approved user")
            if self.first_final_approve_user_id != self.inv_final_approve_user_id:
                self.is_forwarding_approval = True
                self.approve_forwarded = False
            else:
                self.is_forwarding_approval = False

    ########################################################################################################################

    def compute_currency_omr(self):
        """ compute currency to omr"""
        for invoice in self:
            invoice.currency_omr = self.env['res.currency'].search([('name', '=', 'OMR')], limit=1)

    @api.depends('invoice_line_ids')
    def _compute_analytic_distribution(self):
        for move in self:
            if self.invoice_line_ids:
                for move_line in self.invoice_line_ids:
                    if move_line.analytic_distribution:
                        for key, value in move_line.analytic_distribution.items():
                            analytic_id = self.env['account.analytic.account'].search([('id', '=', key)])
                            move.write({
                                'analytic_account_id': analytic_id.id,
                            })
                    else:
                        move.analytic_account_id = False
            else:
                move.analytic_account_id = False

    ########################################################################################################################

    def create_approval_request(self, move, move_type):
        if move:
            is_bill = move_type == 'in_invoice'
            approve_user_id = move.bill_approve_user_id if is_bill else move.inv_approve_user_id

            doc_type = "Vendor bill" if is_bill else "Invoice"
            label = 'Vendor' if is_bill else 'Customer'
            date_label = "Bill Date" if is_bill else "Invoice Date"
            amount_total = f"{move.currency_id.symbol} {'{:,.2f}'.format(move.amount_total)}"

            subject = _('Vendor Bill Approval Request') if is_bill else _('Invoice Approval Request')

            body = _(
                "<p>A {doc_type} is awaiting your approval.</p>"
                "<p><strong>{label}:</strong> {partner}<br/>"
                "<strong>Total Amount:</strong> {amount}<br/>"
                "<strong>{date_label}:</strong> {date}</p>"
            ).format(
                doc_type=doc_type,
                label=label,
                partner=move.partner_id.name,
                amount=amount_total,
                date_label=date_label,
                date=move.invoice_date.strftime('%d/%m/%Y'),
            )

            category_id = False
            if move_type == 'out_invoice':
                category_id = self.env.ref('kg_raw_fisheries_approvals.approval_category_data_invoice').id
            if move_type == 'in_invoice':
                category_id = self.env.ref('kg_raw_fisheries_approvals.approval_category_data_bills').id

            approval_req_id = self.env['approval.request'].create({
                'name': subject,
                'move_id': move.id,
                'request_owner_id': self.env.user.id,
                'category_id': category_id,
                'reason': body,
                'automated_sequence': True,
                'approver_ids': [(0, 0, {
                    'user_id': approve_user_id.id,
                    'required': True,
                    'status': 'new'
                })]
            })
            self.approval_id = approval_req_id.id

            move_attachment_ids = self.env['ir.attachment'].search([('res_id', '=', move.id)])
            for attachment in move_attachment_ids:
                self.env['ir.attachment'].create({
                    'name': attachment.name,
                    'type': attachment.type,
                    'datas': attachment.datas,
                    'res_model': "approval.request",
                    'res_id': approval_req_id.id,
                })

            approval_req_id.action_confirm()

    def action_request_for_approval(self):
        """Request approval for vendor bill or invoice."""
        for move in self:
            if not move.line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_note')):
                raise UserError(_('You need to add a line before posting.'))
            if not move.invoice_date:
                raise ValidationError(
                    _("Please select the %s date !!") % ("bill" if move.move_type == 'in_invoice' else "invoice"))

            is_bill = move.move_type == 'in_invoice'
            approver_id = self.bill_approve_user_id if is_bill else self.inv_approve_user_id

            final_approver_id = self.bill_final_approve_user_id if is_bill else self.inv_final_approve_user_id

            if not approver_id:
                raise ValidationError(
                    _("Select the %s Approver") % ("Bill" if is_bill else "Invoice"))

            if not final_approver_id and self.need_final_approve:
                raise ValidationError(
                    _("Select the %s Final Approver") % ("Bill" if is_bill else "Invoice"))

            move.state = 'approval_requested'
            subject = _('Vendor Bill Approval Request') if is_bill else _('Invoice Approval Request')
            label = 'Vendor' if is_bill else 'Customer'
            date_label = "Bill Date" if is_bill else "Invoice Date"
            doc_type = "Vendor bill" if is_bill else "Invoice"

            self.create_approval_request(move, move.move_type)

            amount_total = f"{move.currency_id.symbol} {'{:,.2f}'.format(move.amount_total)}"
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            approve_url = f"{base_url}/web/action_approve?id={move.id}"
            reject_url = f"{base_url}/web#action=kg_raw_fisheries_accounting.action_reject_reason_wizard&active_id={move.id}"
            forward_url = f"{base_url}/web#action=kg_raw_fisheries_accounting.action_forward_approval_wizard&active_id={move.id}"

            body = _(
                "<p>Dear {name},</p>"
                "<p>A {doc_type} is awaiting your approval.</p>"
                "<p><strong>{label}:</strong> {partner}<br/>"
                "<strong>Total Amount:</strong> {amount}<br/>"
                "<strong>{date_label}:</strong> {date}</p>"
                "<p>Best Regards,<br/>{requester}</p>"
            ).format(
                name=approver_id.name,
                doc_type=doc_type,
                label=label,
                partner=move.partner_id.name,
                amount=amount_total,
                date_label=date_label,
                date=move.invoice_date.strftime('%d/%m/%Y'),
                requester=move.create_uid.name
            )

            buttons = f"""
                    <div>
                        <a href="{approve_url}" style="padding:10px 15px;background:#28a745;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Approve</a>
                        <a href="{reject_url}" style="padding:10px 15px;background:#AF1740;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Reject</a>
                        <a href="{forward_url}" style="padding:10px 15px;background:#0066ff;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Forward</a>
                    </div>
                """

            attachment = self.attach_report(move)

            self.env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': f"<html><body>{body}<br/>{buttons}</body></html>",
                'email_to': approver_id.email,
                'email_from': move.company_id.email,
                'attachment_ids': [(6, 0, attachment)] if attachment else None,
            }).send()

            self.first_approve_user_id = approver_id.id

    def attach_report(self, move):
        move_attachment_ids = self.env['ir.attachment'].search([('res_id', '=', move.id)])
        return move_attachment_ids.ids

    ########################################################################################################################

    def action_forwarding_approval(self):
        self.approve_forwarded = True

        if self.need_final_approve:
            if not self.waiting_final_approve:
                if self.approval_id:
                    self.approval_id.action_cancel()
                self.action_request_for_approval()
            else:
                if self.final_approval_id:
                    self.final_approval_id.action_cancel()
                self.request_final_approve()
        else:
            if self.approval_id:
                self.approval_id.action_cancel()
            self.action_request_for_approval()

    def approve_forward(self):
        is_final = self.need_final_approve and self.waiting_final_approve

        if self.move_type == 'out_invoice':
            users = self.default_inv_final_approve_users_ids if is_final else self.default_inv_approve_users_ids
        else:
            users = self.default_bill_final_approve_users_ids if is_final else self.default_bill_approve_users_ids

        current_user_id = self.first_final_approve_user_id if is_final else self.first_approve_user_id

        return {
            'name': 'Approval Forward',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'forward.approval.wizard',
            'target': 'new',
            'context': {
                'default_current_user_id': current_user_id.id,
                'default_move_id': self.id,
                'default_user_ids': [(6, 0, users.ids)],
            },
        }

    ########################################################################################################################

    def _action_approve_internal(self):
        """Internal Approval Logic without looping back to approval"""
        if self.move_type == 'in_invoice':
            if self.env.user.id != self.bill_approve_user_id.id:
                raise UserError(_("You have no access to approve"))

        if self.move_type == 'out_invoice':
            if self.env.user.id != self.inv_approve_user_id.id:
                raise UserError(_("You have no access to approve"))

        if self.need_final_approve:
            if not self.waiting_final_approve:
                self.waiting_final_approve = True
                self.request_final_approve()
        else:
            self.state = 'approved'

    def action_approve(self):
        """Function for Approval"""
        self.approval_id.action_approve()
        self._action_approve_internal()

    ########################################################################################################################

    def create_final_approval_request(self, move, move_type):
        if move:
            is_bill = move_type == 'in_invoice'
            final_approve_user_id = move.bill_final_approve_user_id if is_bill else move.inv_final_approve_user_id

            doc_type = "Vendor bill" if is_bill else "Invoice"
            label = 'Vendor' if is_bill else 'Customer'
            date_label = "Bill Date" if is_bill else "Invoice Date"
            amount_total = f"{move.currency_id.symbol} {'{:,.2f}'.format(move.amount_total)}"

            subject = _('Vendor Bill Final Approval Request') if is_bill else _('Invoice Final Approval Request')

            body = _(
                "<p>A {doc_type} is awaiting your final approval.</p>"
                "<p><strong>{label}:</strong> {partner}<br/>"
                "<strong>Total Amount:</strong> {amount}<br/>"
                "<strong>{date_label}:</strong> {date}</p>"
            ).format(
                doc_type=doc_type,
                label=label,
                partner=move.partner_id.name,
                amount=amount_total,
                date_label=date_label,
                date=move.invoice_date.strftime('%d/%m/%Y'),
            )

            category_id = False
            if move_type == 'out_invoice':
                category_id = self.env.ref('kg_raw_fisheries_approvals.approval_category_data_invoice').id
            if move_type == 'in_invoice':
                category_id = self.env.ref('kg_raw_fisheries_approvals.approval_category_data_bills').id

            approval_req_id = self.env['approval.request'].create({
                'name': subject,
                'move_id': move.id,
                'request_owner_id': self.env.user.id,
                'category_id': category_id,
                'reason': body,
                'automated_sequence': True,
                'approver_ids': [(0, 0, {
                    'user_id': final_approve_user_id.id,
                    'required': True,
                    'status': 'new'
                })]
            })

            self.final_approval_id = approval_req_id.id

            move_attachment_ids = self.env['ir.attachment'].search([('res_id', '=', move.id)])
            for attachment in move_attachment_ids:
                self.env['ir.attachment'].create({
                    'name': attachment.name,
                    'type': attachment.type,
                    'datas': attachment.datas,
                    'res_model': "approval.request",
                    'res_id': approval_req_id.id,
                })

            approval_req_id.action_confirm()

    def request_final_approve(self):
        for move in self:
            is_bill = move.move_type == 'in_invoice'
            subject = _('Vendor Bill Final Approval Request') if is_bill else _('Invoice Final Approval Request')
            label = 'Vendor' if is_bill else 'Customer'
            date_label = "Bill Date" if is_bill else "Invoice Date"
            doc_type = "Vendor bill" if is_bill else "Invoice"

            self.create_final_approval_request(move, move.move_type)

            final_approver_id = self.bill_final_approve_user_id if is_bill else self.inv_final_approve_user_id

            amount_total = f"{move.currency_id.symbol} {'{:,.2f}'.format(move.amount_total)}"
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            approve_url = f"{base_url}/web/action_final_approve?id={move.id}"
            reject_url = f"{base_url}/web#action=kg_raw_fisheries_accounting.action_final_reject_reason_wizard&active_id={move.id}"
            forward_url = f"{base_url}/web#action=kg_raw_fisheries_accounting.action_final_forward_approval_wizard&active_id={move.id}"

            body = _(
                "<p>Dear {name},</p>"
                "<p>A {doc_type} is awaiting your final approval.</p>"
                "<p><strong>{label}:</strong> {partner}<br/>"
                "<strong>Total Amount:</strong> {amount}<br/>"
                "<strong>{date_label}:</strong> {date}</p>"
                "<p>Best Regards,<br/>{requester}</p>"
            ).format(
                name=final_approver_id.name,
                doc_type=doc_type,
                label=label,
                partner=move.partner_id.name,
                amount=amount_total,
                date_label=date_label,
                date=move.invoice_date.strftime('%d/%m/%Y'),
                requester=move.create_uid.name
            )

            buttons = f"""
                                <div>
                                    <a href="{approve_url}" style="padding:10px 15px;background:#28a745;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Approve</a>
                                    <a href="{reject_url}" style="padding:10px 15px;background:#AF1740;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Reject</a>
                                    <a href="{forward_url}" style="padding:10px 15px;background:#0066ff;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">Forward</a>
                                </div>
                            """

            attachment = self.attach_report(move)

            self.env['mail.mail'].sudo().create({
                'subject': subject,
                'body_html': f"<html><body>{body}<br/>{buttons}</body></html>",
                'email_to': final_approver_id.email,
                'email_from': move.company_id.email,
                'attachment_ids': [(6, 0, attachment)] if attachment else None,
            }).send()

            self.first_final_approve_user_id = final_approver_id.id

    def _action_final_approve_internal(self):
        if self.move_type == 'in_invoice':
            if self.env.user.id != self.bill_final_approve_user_id.id:
                raise UserError(_("You have no access to approve"))

        if self.move_type == 'out_invoice':
            if self.env.user.id != self.inv_final_approve_user_id.id:
                raise UserError(_("You have no access to approve"))

        self.state = 'approved'

    def action_final_approve(self):
        self._action_final_approve_internal()
        self.final_approval_id.action_approve()

    ########################################################################################################################

    def action_reject(self):
        context = {'default_in_form': True}

        if self.need_final_approve and self.waiting_final_approve:
            context['default_is_final_approve'] = True

        return {
            'name': 'Reject Reason',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'reject.reason.wizard',
            'target': 'new',
            'context': context,
        }

    ########################################################################################################################

    @api.depends('invoice_line_ids')
    def _compute_label_invoice_line(self):
        """To compute the label of 1st account move line to show in tree view"""
        for record in self:
            first_line = record.invoice_line_ids and record.invoice_line_ids[0]
            record.label_invoice_line = first_line and first_line.name or ''

    @api.depends('date', 'auto_post')
    def _compute_hide_post_button(self):
        for record in self:
            if record.move_type == 'out_invoice' and record.need_invoice_approve:
                record.hide_post_button = record.state != 'approved' or record.auto_post != 'no' and record.date > fields.Date.context_today(
                    record)
            elif record.move_type == 'in_invoice' and record.need_bill_approve:
                record.hide_post_button = record.state != 'approved' or record.auto_post != 'no' and record.date > fields.Date.context_today(
                    record)
            else:
                record.hide_post_button = record.state != 'draft' or record.auto_post != 'no' and record.date > fields.Date.context_today(
                    record)

    def action_post(self):
        if self.move_type == 'out_invoice' and self.need_invoice_approve:
            if self.state == 'rejected':
                raise ValidationError(_("You cannot confirm because your request has been rejected"))
            if self.state != 'approved':
                raise ValidationError(_("You cannot do this action without approval"))

        if self.move_type == 'in_invoice' and self.need_bill_approve:
            if self.state == 'rejected':
                raise ValidationError(_("You cannot confirm because your request has been rejected"))
            if self.state != 'approved':
                raise ValidationError(_("You cannot do this action without approval"))

        return super(AccountMove, self).action_post()

    def _post(self, soft=True):
        for rec in self:
            if rec.move_type == 'out_invoice' and rec.need_invoice_approve:
                if rec.state == 'rejected':
                    raise ValidationError(_("You cannot confirm because your request has been rejected"))
                if rec.state != 'approved':
                    raise ValidationError(_("You cannot do this action without approval"))

            if rec.move_type == 'in_invoice' and rec.need_bill_approve:
                if rec.state == 'rejected':
                    raise ValidationError(_("You cannot confirm because your request has been rejected"))
                if rec.state != 'approved':
                    raise ValidationError(_("You cannot do this action without approval"))
        return super(AccountMove, self)._post(soft)

    @api.model
    def approve_data(self, move):
        if move:
            move_id = self.env['account.move'].search([('id', '=', move)], limit=1)
            if move_id:
                move_id.action_approve()

    @api.model
    def export_approval_request_report(self):
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model', 'account.move')

        file_io = BytesIO()
        workbook = xlsxwriter.Workbook(file_io)
        self.generate_xlsx_report(workbook, data={'ids': active_ids, 'model': active_model})
        workbook.close()

        fout = encodebytes(file_io.getvalue())
        file_io.close()

        report_name = 'Accounts - Pending Approvals Report.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': report_name,
            'type': 'binary',
            'datas': fout,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': f'/web/content/{attachment.id}?download=true',
        }

    def generate_xlsx_report(self, workbook, data=None):
        sheet = workbook.add_worksheet('Pending Approvals Report')

        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 50)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)

        num_format = workbook.add_format({'num_format': '0.00', 'align': 'right', 'border': 1})

        bold_right_format = workbook.add_format({'align': 'right', 'bold': True, 'border': 1})

        bold_left_format = workbook.add_format({'align': 'left', 'bold': True, 'border': 1})
        left_format = workbook.add_format({'align': 'left', 'border': 1})
        bold_left_grey_format = workbook.add_format(
            {'align': 'left', 'bold': True, 'border': 1, 'bg_color': '#a6a6a6'})
        bold_left_green_format = workbook.add_format(
            {'align': 'left', 'bold': True, 'border': 1, 'bg_color': '#b2b266'})
        bold_left_brown_format = workbook.add_format(
            {'align': 'left', 'bold': True, 'border': 1, 'bg_color': '#d2a679'})

        bold_center_format = workbook.add_format({'align': 'center', 'bold': True, 'border': 1})
        center_format = workbook.add_format({'align': 'center', 'border': 1})
        bold_center_orange_format = workbook.add_format(
            {'align': 'center', 'bold': True, 'border': 1, 'bg_color': '#ffb84d', 'font_size': 15})
        bold_center_blue_format = workbook.add_format(
            {'align': 'center', 'bold': True, 'border': 1, 'bg_color': '#ccf2ff'})

        row = 0
        col = 0

        sheet.merge_range(row, col, row, col + 7, 'Pending Approvals Report', bold_center_orange_format)
        row = row + 2

        move_ids = self.env["account.move"].search(
            [('state', '=', 'approval_requested'), ('move_type', 'in', ['in_invoice', 'out_invoice'])])

        company_currency = self.env.company.currency_id.name

        if move_ids:
            invoice_approver_user_ids = move_ids.mapped('inv_approve_user_id')
            invoice_final_approver_user_ids = move_ids.mapped('inv_final_approve_user_id')

            bill_approver_user_ids = move_ids.mapped('bill_approve_user_id')
            bill_final_approver_user_ids = move_ids.mapped('bill_final_approve_user_id')

            user_ids = invoice_approver_user_ids | invoice_final_approver_user_ids | bill_approver_user_ids | bill_final_approver_user_ids

            if user_ids:
                for usr in user_ids:
                    sheet.merge_range(row, col, row, col + 7, usr.name, bold_left_grey_format)
                    row = row + 1

                    invoice_approver_ids = move_ids.filtered(
                        lambda x: x.inv_approve_user_id.id == usr.id and not x.waiting_final_approve)

                    invoice_final_approver_ids = move_ids.filtered(
                        lambda x: x.inv_final_approve_user_id.id == usr.id and x.waiting_final_approve)

                    if invoice_approver_ids or invoice_final_approver_ids:
                        sheet.merge_range(row, col, row, col + 7, 'Invoices', bold_left_green_format)
                        row = row + 1

                        if invoice_approver_ids:
                            sheet.merge_range(row, col + 1, row, col + 7, 'Invoice Approvals', bold_center_blue_format)
                            row = row + 1

                            if invoice_approver_ids:
                                sheet.write(row, col + 1, 'Number', bold_center_format)
                                sheet.write(row, col + 2, 'Customer', bold_left_format)
                                sheet.write(row, col + 3, 'Invoice Date', bold_center_format)
                                sheet.write(row, col + 4, 'Due Date', bold_center_format)
                                sheet.write(row, col + 5, 'Currency', bold_center_format)
                                sheet.write(row, col + 6, 'Total', bold_right_format)
                                sheet.write(row, col + 7, 'Total Signed - ' + str(company_currency),
                                            bold_right_format)
                                row = row + 1

                                for inv in invoice_approver_ids:
                                    sheet.write(row, col + 1, inv.kg_invoice_no if inv.kg_invoice_no else inv.name,
                                                center_format)
                                    sheet.write(row, col + 2, inv.partner_id.name, left_format)
                                    sheet.write(row, col + 3,
                                                datetime.strptime(str(inv.invoice_date), '%Y-%m-%d').strftime(
                                                    '%m-%d-%Y') if inv.invoice_date else '', center_format)
                                    sheet.write(row, col + 4,
                                                datetime.strptime(str(inv.invoice_date_due), '%Y-%m-%d').strftime(
                                                    '%m-%d-%Y') if inv.invoice_date_due else '', center_format)
                                    sheet.write(row, col + 5, inv.currency_id.name, center_format)
                                    sheet.write(row, col + 6, inv.amount_total, num_format)
                                    sheet.write(row, col + 7, inv.amount_total_signed, num_format)
                                    row = row + 1
                                row = row + 1

                        if invoice_final_approver_ids:
                            sheet.merge_range(row, col + 1, row, col + 7, 'Invoice Final Approvals',
                                              bold_center_blue_format)
                            row = row + 1

                            if invoice_final_approver_ids:
                                sheet.write(row, col + 1, 'Number', bold_center_format)
                                sheet.write(row, col + 2, 'Customer', bold_left_format)
                                sheet.write(row, col + 3, 'Invoice Date', bold_center_format)
                                sheet.write(row, col + 4, 'Due Date', bold_center_format)
                                sheet.write(row, col + 5, 'Currency', bold_center_format)
                                sheet.write(row, col + 6, 'Total', bold_right_format)
                                sheet.write(row, col + 7, 'Total Signed - ' + str(company_currency), bold_right_format)
                                row = row + 1

                                for inv_final in invoice_final_approver_ids:
                                    sheet.write(row, col + 1,
                                                inv_final.kg_invoice_no if inv_final.kg_invoice_no else inv_final.name,
                                                center_format)
                                    sheet.write(row, col + 2, inv_final.partner_id.name, left_format)
                                    sheet.write(row, col + 3,
                                                datetime.strptime(str(inv_final.invoice_date), '%Y-%m-%d').strftime(
                                                    '%m-%d-%Y') if inv_final.invoice_date else '', center_format)
                                    sheet.write(row, col + 4,
                                                datetime.strptime(str(inv_final.invoice_date_due), '%Y-%m-%d').strftime(
                                                    '%m-%d-%Y') if inv_final.invoice_date_due else '', center_format)
                                    sheet.write(row, col + 5, inv_final.currency_id.name, center_format)
                                    sheet.write(row, col + 6, inv_final.amount_total, num_format)
                                    sheet.write(row, col + 7, inv_final.amount_total_signed, num_format)
                                    row = row + 1
                                row = row + 1

                    bill_approver_ids = move_ids.filtered(
                        lambda x: x.bill_approve_user_id.id == usr.id and not x.waiting_final_approve)

                    bill_final_approver_ids = move_ids.filtered(
                        lambda x: x.bill_final_approve_user_id.id == usr.id and x.waiting_final_approve)

                    if bill_approver_ids or bill_final_approver_ids:
                        sheet.merge_range(row, col, row, col + 7, 'Bills', bold_left_brown_format)
                        row = row + 1

                        if bill_approver_ids:
                            sheet.merge_range(row, col + 1, row, col + 7, 'Bills Approvals', bold_center_blue_format)
                            row = row + 1

                            sheet.write(row, col + 1, 'Number', bold_center_format)
                            sheet.write(row, col + 2, 'Customer', bold_left_format)
                            sheet.write(row, col + 3, 'Invoice Date', bold_center_format)
                            sheet.write(row, col + 4, 'Due Date', bold_center_format)
                            sheet.write(row, col + 5, 'Currency', bold_center_format)
                            sheet.write(row, col + 6, 'Total', bold_right_format)
                            sheet.write(row, col + 7, 'Total Signed - ' + str(company_currency), bold_right_format)
                            row = row + 1

                            for bill in bill_approver_ids:
                                sheet.write(row, col + 1, bill.kg_invoice_no if bill.kg_invoice_no else bill.name,
                                            center_format)
                                sheet.write(row, col + 2, bill.partner_id.name, left_format)
                                sheet.write(row, col + 3,
                                            datetime.strptime(str(bill.invoice_date), '%Y-%m-%d').strftime(
                                                '%m-%d-%Y') if bill.invoice_date else '', center_format)
                                sheet.write(row, col + 4,
                                            datetime.strptime(str(bill.invoice_date_due), '%Y-%m-%d').strftime(
                                                '%m-%d-%Y') if bill.invoice_date_due else '', center_format)
                                sheet.write(row, col + 5, bill.currency_id.name, center_format)
                                sheet.write(row, col + 6, bill.amount_total, num_format)
                                sheet.write(row, col + 7, abs(bill.amount_total_signed), num_format)
                                row = row + 1
                            row = row + 1

                        if bill_final_approver_ids:
                            sheet.merge_range(row, col + 1, row, col + 7, 'Bills Final Approvals',
                                              bold_center_blue_format)
                            row = row + 1

                            sheet.write(row, col + 1, 'Number', bold_center_format)
                            sheet.write(row, col + 2, 'Customer', bold_left_format)
                            sheet.write(row, col + 3, 'Invoice Date', bold_center_format)
                            sheet.write(row, col + 4, 'Due Date', bold_center_format)
                            sheet.write(row, col + 5, 'Currency', bold_center_format)
                            sheet.write(row, col + 6, 'Total', bold_right_format)
                            sheet.write(row, col + 7, 'Total Signed - ' + str(company_currency), bold_right_format)
                            row = row + 1

                            for bill_final in bill_final_approver_ids:
                                sheet.write(row, col + 1,
                                            bill_final.kg_invoice_no if bill_final.kg_invoice_no else bill_final.name,
                                            center_format)
                                sheet.write(row, col + 2, bill_final.partner_id.name, left_format)
                                sheet.write(row, col + 3,
                                            datetime.strptime(str(bill_final.invoice_date), '%Y-%m-%d').strftime(
                                                '%m-%d-%Y') if bill_final.invoice_date else '', center_format)
                                sheet.write(row, col + 4,
                                            datetime.strptime(str(bill_final.invoice_date_due), '%Y-%m-%d').strftime(
                                                '%m-%d-%Y') if bill_final.invoice_date_due else '', center_format)
                                sheet.write(row, col + 5, bill_final.currency_id.name, center_format)
                                sheet.write(row, col + 6, bill_final.amount_total, num_format)
                                sheet.write(row, col + 7, abs(bill_final.amount_total_signed), num_format)
                                row = row + 1
                            row = row + 1

    @api.model
    def get_pending_approvals_data(self):
        result = []
        move_id = self.env["account.move"].search(
            [('state', '=', 'approval_requested'), ('move_type', 'in', ['in_invoice', 'out_invoice'])])
        if move_id:
            for move in move_id:
                if move.waiting_final_approve:
                    approver = move.inv_final_approve_user_id.name or move.bill_final_approve_user_id.name
                    state = 'Waiting Invoice Final Approval' if move.move_type == 'out_invoice' else 'Waiting Bill Final Approval'
                else:
                    approver = move.inv_approve_user_id.name or move.bill_approve_user_id.name
                    state = 'Waiting Invoice Approval' if move.move_type == 'out_invoice' else 'Waiting Bill Approval'

                move_type = 'bill' if move.move_type == 'in_invoice' else 'invoice'
                if approver:
                    result.append({
                        'id': move.id,
                        'no': move.kg_invoice_no if move.kg_invoice_no else move.name,
                        'partner': move.partner_id.name,
                        'vessel': move.vessel_id.name,
                        'batch': move.batch_info,
                        'approver': approver,
                        'move_type': move_type,
                        'invoice_date': move.invoice_date.strftime('%d-%m-%Y') if move.invoice_date else '',
                        'due_date': move.invoice_date_due.strftime('%d-%m-%Y') if move.invoice_date_due else '',
                        'total': abs(move.amount_total_signed),
                        'state': state
                    })
        return result

    def _get_invoice_legal_documents(self):
        self.ensure_one()
        if self.invoice_pdf_report_id:
            attachments = self.env['account.move.send']._get_invoice_extra_attachments(self)
        else:
            content, _ = self.env['ir.actions.report']._render('kg_raw_fisheries_accounting.action_report_tax_invoice',
                                                               self.ids, data={'proforma': True})
            attachments = self.env['ir.attachment'].new({
                'raw': content,
                'name': self._get_invoice_proforma_pdf_report_filename(),
                'mimetype': 'application/pdf',
                'res_model': self._name,
                'res_id': self.id,
            })
        return attachments

    def get_invoice_pdf_report_attachment(self):
        if len(self) < 2 and self.invoice_pdf_report_id:
            return self.invoice_pdf_report_id.raw, self.invoice_pdf_report_id.name
        elif len(self) < 2 and self.message_main_attachment_id:
            return self.message_main_attachment_id.raw, self.message_main_attachment_id.name
        pdf_content = \
            self.env['ir.actions.report']._render('kg_raw_fisheries_accounting.action_report_tax_invoice', self.ids)[0]
        pdf_name = self._get_invoice_report_filename() if len(self) == 1 else "Invoices.pdf"
        return pdf_content, pdf_name


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    supplier_tax_id = fields.Char(string='Supplier TaxID', related='partner_id.vat', store=True)
