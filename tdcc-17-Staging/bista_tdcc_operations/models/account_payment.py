# -*- encoding: utf-8 -*-
#
#
# Bista Solutions Pvt. Ltd
# Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
import base64

from odoo import models, fields, api, _
import warnings
from datetime import datetime, date

from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        if self._context.get('active_model', False) == 'account.move':
            active_id = self._context.get('active_id')
            invoice = self.env['account.move'].browse(active_id)
            rec.update({
                'user_id': invoice.user_id.id or False,
                'physician_id': invoice.user_id.partner_id.id or False,
            })
        return rec

    @api.depends()
    def _get_available_balance(self):
        for payment in self:

            if payment.payment_type == 'inbound':
                cml_id = payment.line_ids.filtered(
                    lambda ml: ml.account_id.account_type == 'asset_receivable')
                payment.available_balance = abs(
                    cml_id.amount_residual) if cml_id else 0.00
            else:
                payment.available_balance = 00

    service_type_id = fields.Many2one('service.type', string="Service Type",
                                      copy=False)
    physician_id = fields.Many2one('res.partner',
                                   string='Physician',
                                   domain=[('is_physician', '=', True)])
    physician_type = fields.Selection([('single', 'Single'),
                                       ('multi', 'Multi')],
                                      string='Physician Type',
                                      default='single')
    multi_physician_ids = fields.One2many('account.payment.physician',
                                          'payment_id',
                                          string='Practitioners ')
    payment_info = fields.Char(string='Payment Information')
    tdcc_voucher_id = fields.Integer(string="TDCC Voucher Ref.")
    tdcc_voucher_sequence = fields.Char(string="TDCC Voucher No.")
    tdcc_cheque_date = fields.Date(string='TDCC Cheque Date')
    tdcc_cheque_due_date = fields.Date(string='TDCC Cheque Due Date')
    tdcc_cheque_no = fields.Char(string='TDCC Cheque Number')
    allow_cancel = fields.Boolean(string="Allow Cancel")
    payment_cancel_req_user_id = fields.Many2one('res.users',
                                                 string="Cancel Request By")
    payment_cancel_req_date = fields.Datetime(string="Cancel Request Date")
    payment_cancel_req_sent = fields.Boolean(string="Cancel Request sent")
    cancel_reason = fields.Text(string="Cancel Reason")
    approval_by = fields.Many2one('res.users', string="Approved By")
    approval_date = fields.Datetime(string="Approval Date")
    cancelled_by = fields.Many2one('res.users', string="Cancelled By")
    cancelled_date = fields.Datetime(string="Date Canceled")
    available_balance = fields.Float(string="Available Balance",
                                     compute=_get_available_balance)
    invoice_ids = fields.Many2many('account.move')


    def cancel(self):
        """ Check if payment cancellation approved by co-founder or it is
        from PDC bounce cheque"""
        if not self.allow_cancel and not self._context.get('cheque_bounce') and \
            self.partner_type == 'customer' and self.payment_type == 'inbound':
            raise UserError(_('You can not cancel payment \
                                untill approved by Co-founders'))
        self.write({'cancelled_by': self.env.user.id,
                    'cancelled_date': datetime.now()})
        return super(AccountPayment, self).cancel()


    def action_draft(self):
        self.write({'payment_cancel_req_date': False,
                    'payment_cancel_req_sent': False,
                    'allow_cancel': False})
        return super(AccountPayment, self).action_draft()


    def action_approve_cancel_payment(self):
        cofounder_group_id = 'bista_tdcc_operations.group_tdcc_cofounder'
        if self.env.user.has_group(cofounder_group_id):
            if not self.payment_cancel_req_sent:
                raise UserError(_('You can not perform this action without request for cancellation'))
            self.write({'allow_cancel': True,
                        'approval_by': self.env.user.id,
                        'approval_date': datetime.now()})
        else:
            raise UserError(_('You are not allowed to approve cancel payment request'))


    def action_send_payment_mail(self):
        self.ensure_one()
        try:
            template_id = self.env.ref(
                'bista_tdcc_operations.account_payment_mail_template_with_attachment')
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref(
                'mail.email_compose_message_wizard_form')
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'account.payment',
             'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id and template_id.id,
            'default_composition_mode': 'comment',
            # 'custom_layout': "mail.mail_notification_borders",
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id.id, 'form')],
            'view_id': compose_form_id.id,
            'target': 'new',
            'context': ctx,
        }

    def action_post(self):
        posted = super().action_post()

        if len(self) > 1:
            for rec in self:
                rec._process_single_record()
        else:
            for rec in self:
                rec.service_type_id = rec.service_type_id or False
                if rec.payment_type == 'inbound' and rec.partner_type == 'customer' and rec.payment_method_code != 'pdc':
                    subject = "Payment Received"
                    email_from = rec.env.user.partner_id.email or ''
                    email_to = rec.partner_id.email
                    if rec.partner_id.is_student:
                        greeting = f"Dear {rec.partner_id.father_name or rec.partner_id.mother_name or 'Parents'},"
                    else:
                        greeting = f"Dear {rec.partner_id.name},"
                    body_html = f"""
                          <div>
                              <p>{greeting}</p>
                              <br/><br/>
                              Today we have received the following payment details:<br/><br/>
                              <strong>Payment Date:</strong> {rec.date}<br/><br/>
                              <strong>Receipt No:</strong> {rec.name}<br/><br/>
                              <strong>Receipt Amount:</strong> {rec.amount} AED<br/>
                              <br/><br/><br/>
                              Thank you and have a lovely day.<br/><br/>
                          </div>
                      """
                    message = self.env['mail.message'].create({
                        'model': self._name,
                        'res_id': self.id,
                        'subject': subject,
                        'body': body_html,
                        'author_id': self.env.user.partner_id.id,
                    })
                    pdf_content = \
                    self.env['ir.actions.report']._render_qweb_pdf("bista_tdcc_operations.mail_report_payment_form",
                                                                   self.id)[0]
                    pdf_content_base64 = base64.b64encode(pdf_content).decode('utf-8')
                    attachment_name = f"payment_report_{self.id}.pdf"
                    attachment = self.env['ir.attachment'].create({
                        'name': attachment_name,
                        'mimetype': 'application/pdf',
                        'datas': pdf_content_base64,
                    })

                    self.env['mail.thread'].message_notify(
                        partner_ids=[rec.partner_id.id],
                        body=message.body,
                        subject=message.subject,
                        record_name=self.name,
                        model_description=self._description,
                        force_send=True,
                        attachment_ids=[attachment.id]
                    )

                    # # Send the email with the attachment
                    # mail_values = {
                    #     'subject': subject,
                    #     'recipient_ids' : [(6,0,rec.partner_id.ids)],
                    #     'body_html': body_html,
                    #     'email_from': email_from,
                    #     'email_to': email_to,
                    #     'auto_delete': False,
                    #     'attachment_ids': [(6, 0, [attachment.id])]  # Attach the file to the email
                    # }
                    # mail = self.env['mail.mail'].create(mail_values)
                    # mail.send()

        return posted

    def _process_single_record(self):
        """
        This method ensures the processing is done for a single record.
        """
        for rec in self:
            rec.service_type_id = rec.service_type_id or False
            if rec.payment_type == 'inbound' and rec.partner_type == 'customer' and rec.payment_method_code != 'pdc':
                subject = "Payment Received"
                email_from = rec.env.user.partner_id.email or ''
                email_to = rec.partner_id.email
                if rec.partner_id.is_student:
                    greeting = f"Dear {rec.partner_id.father_name or rec.partner_id.mother_name or 'Parents'},"
                else:
                    greeting = f"Dear {rec.partner_id.name},"
                body_html = f"""
                      <div>
                          <p>{greeting}</p>
                          <br/><br/>
                          Today we have received the following payment details:<br/><br/>
                          <strong>Payment Date:</strong> {rec.date}<br/><br/>
                          <strong>Receipt No:</strong> {rec.name}<br/><br/>
                          <strong>Receipt Amount:</strong> {rec.amount} AED<br/>
                          <br/><br/><br/>
                          Thank you and have a lovely day.<br/><br/>
                      </div>
                  """
                message = self.env['mail.message'].create({
                    'model': self._name,
                    'res_id': self.id,
                    'subject': subject,
                    'body': body_html,
                    'author_id': self.env.user.partner_id.id,
                })
                pdf_content = \
                self.env['ir.actions.report']._render_qweb_pdf("bista_tdcc_operations.mail_report_payment_form",
                                                               self.id)[0]
                pdf_content_base64 = base64.b64encode(pdf_content).decode('utf-8')
                attachment_name = f"payment_report_{self.id}.pdf"
                attachment = self.env['ir.attachment'].create({
                    'name': attachment_name,
                    'mimetype': 'application/pdf',
                    'datas': pdf_content_base64,
                })

                self.env['mail.thread'].message_notify(
                    partner_ids=[rec.partner_id.id],
                    body=message.body,
                    subject=message.subject,
                    record_name=self.name,
                    model_description=self._description,
                    force_send=True,
                    attachment_ids=[attachment.id]
                )

    @api.constrains('amount', 'multi_physician_ids', 'physician_type')
    def check_multi_physician_amount(self):
        for rec in self:
            if rec.physician_type == 'multi' and rec.multi_physician_ids:
                total_amt = 0.0
                for phy in rec.multi_physician_ids:
                    total_amt += phy.amount
                if rec.amount != total_amt:
                    raise UserError(_('Practitioners total amount and Payment total amount must be same.'))

    @api.onchange('physician_type')
    def onchange_physician_type(self):
        if self.physician_type and self.physician_type == 'single':
            self.multi_physician_ids = False
        elif self.physician_type and self.physician_type == 'multi':
            self.physician_id = False


    def view_open_invoices(self):
        return {
            'name': _('Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('partner_id', '=', self.partner_id.id),
                       ('state', '=', 'open'), ('move_type', '=', 'out_invoice')],
        }


    def get_advance_payment_amount(self):
        amount = 0.00
        for payment in self:
            cml_id = payment.line_ids.filtered(
                lambda ml: ml.account_id.account_type == 'receivable')
            amount = abs(cml_id.amount_residual)
        return amount

    def get_vendor_payment_amount(self):
        amount = 0.00
        for payment in self:
            debit_line_id = payment.move_line_ids.filtered(
                lambda ml: ml.account_id.internal_type == 'payable')
            amount = abs(debit_line_id.debit - debit_line_id.amount_residual)
            if self._context.get('invoice_id'):
                invoice_id = self.env['account.move'].browse(
                    self._context.get('invoice_id'))
                payment_log_id = invoice_id.payment_log_ids.filtered(
                    lambda line: line.payment_id and line.payment_id.id != self.id and line.date <= date.today())
                paid_amount = sum(
                    line.amount for line in payment_log_id) or 0.00
                return paid_amount
        return amount

    def action_validate_invoice_payment(self):
        res = super(AccountPayment, self).action_validate_invoice_payment()
        invoice_id = self.env['account.move'].browse(
            self._context.get('active_id'))
        vals = {'invoice_id': invoice_id.id, 'payment_id': self.id,
                'amount': self.amount, 'date': self.payment_date}
        if invoice_id.move_type == 'in_invoice':
            debit_aml = invoice_id.payment_move_line_ids.filtered(
                lambda aml: aml.account_id.id == invoice_id.account_id.id
                        and aml.debit != 0.00)
            vals.update({'move_line_id': debit_aml and debit_aml[0].id})
        if invoice_id.move_type == 'out_invoice':
            credit_aml = invoice_id.payment_move_line_ids.filtered(
                lambda aml: aml.account_id.id == invoice_id.account_id.id
                        and aml.credit != 0.00)
            vals.update({'move_line_id': credit_aml and credit_aml[0].id})
        invoice_id.write({'payment_log_ids': [(0, 0, vals)]})
        return res


class AccountPaymentPhysician(models.Model):
    _name = 'account.payment.physician'
    _description = 'Account Payment Physician'

    physician_id = fields.Many2one('res.partner', string='Practitioner')
    amount = fields.Float(string='amount')
    payment_id = fields.Many2one('account.payment',
                                 string='Account Payment')


class account_register_payments(models.TransientModel):
    _inherit = "account.payment.register"

    physician_id = fields.Many2one('res.partner',
                                   string='Physician',
                                   domain=[('is_physician', '=', True)])
    physician_type = fields.Selection([('single', 'Single'),
                                       ('multi', 'Multi')],
                                      string='Physician Type',
                                      default='single')

    multi_physician_ids = fields.One2many('account.payment.physician',
                                          'payment_id',
                                          string='Practitioners ')
    user_id = fields.Many2one('res.users', string='Salesperson')
    service_type_id = fields.Many2one('service.type', string='Service Type')

    def _create_payments(self):
        self.ensure_one()
        all_batches = self._get_batches()
        batches = []
        move_id = self.line_ids.mapped('move_id')[:1]

        # Skip batches that are not valid (bank account not trusted but required)
        for batch in all_batches:
            batch_account = self._get_batch_account(batch)
            if self.require_partner_bank_account and not batch_account.allow_out_payment:
                continue
            batches.append(batch)

        if not batches:
            raise UserError(
                _('To record payments with %s, the recipient bank account must be manually validated. You should go on the partner bank account in order to validate it.',
                  self.payment_method_line_id.name))

        first_batch_result = batches[0]
        edit_mode = self.can_edit_wizard and (len(first_batch_result['lines']) == 1 or self.group_payment)
        to_process = []

        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard(first_batch_result)

            # Add your custom vals update here for the edit_mode case
            payment_vals.update({
                'physician_type': self.physician_type,
                'physician_id': self.physician_id.id if self.physician_id else False,
                'multi_physician_ids': [(6, 0, self.multi_physician_ids.ids)] if self.multi_physician_ids else False,
                'service_type_id': self.service_type_id.id if self.service_type_id else False,
                'invoice_ids':move_id,
            })

            to_process_values = {
                'create_vals': payment_vals,
                'to_reconcile': first_batch_result['lines'],
                'batch': first_batch_result,
            }

            # Force the rate during the reconciliation to put the difference directly on the exchange difference.
            if self.writeoff_is_exchange_account and self.currency_id == self.company_currency_id:
                total_batch_residual = sum(first_batch_result['lines'].mapped('amount_residual_currency'))
                to_process_values['rate'] = abs(total_batch_residual / self.amount) if self.amount else 0.0

            to_process.append(to_process_values)
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'payment_values': {
                                **batch_result['payment_values'],
                                'payment_type': 'inbound' if line.balance > 0 else 'outbound'
                            },
                            'lines': line,
                        })
                batches = new_batches

            for batch_result in batches:
                # Add your custom vals update here for the else case
                batch_payment_vals = self._create_payment_vals_from_batch(batch_result)
                batch_payment_vals.update({
                    'physician_type': self.physician_type,
                    'physician_id': self.physician_id.id if self.physician_id else False,
                    'multi_physician_ids': [
                        (6, 0, self.multi_physician_ids.ids)] if self.multi_physician_ids else False,
                    'service_type_id': self.service_type_id.id if self.service_type_id else False,
                })

                to_process.append({
                    'create_vals': batch_payment_vals,
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })

        payments = self._init_payments(to_process, edit_mode=edit_mode)
        self._post_payments(to_process, edit_mode=edit_mode)
        self._reconcile_payments(to_process, edit_mode=edit_mode)
        return payments

    @api.onchange('physician_type')
    def onchange_physician_type(self):
        if self.physician_type and self.physician_type == 'single':
            self.multi_physician_ids = False
        elif self.physician_type and self.physician_type == 'multi':
            self.physician_id = False


    def create_payments(self):
        res = super(account_register_payments, self).create_payments()
        inv_pay_log = self.env['invoice.payment.log']
        for invoice in self.invoice_ids:
            if invoice.move_type == 'in_invoice':
                aml_id = invoice.payment_move_line_ids.filtered(
                    lambda aml: aml.account_id.id == invoice.account_id.id
                    and aml.debit != 0.00)
                partial_reconcile_credit_id = aml_id and aml_id[0].matched_credit_ids.filtered(
                    lambda cml: cml.credit_move_id.invoice_id.id == invoice.id)
                if partial_reconcile_credit_id:
                    amount = partial_reconcile_credit_id.amount
                else:
                    amount = aml_id and aml_id[0].debit or 0.00
            if invoice.move_type == 'out_invoice':
                aml_id = invoice.payment_move_line_ids.filtered(
                    lambda aml: aml.account_id.id == invoice.account_id.id
                    and aml.credit != 0.00)
                reconcile_cr_id = aml_id and aml_id[0].matched_debit_ids.filtered(
                    lambda dml: dml.debit_move_id.invoice_id.id == invoice.id)
                if reconcile_cr_id:
                    amount = sum(reconcile_cr_id.mapped('amount')) or 0.00
                else:
                    amount = aml_id and aml_id[0].credit or 0.00
            inv_pay_log_id = inv_pay_log.search([
                ('payment_id', '=', aml_id and aml_id[0].payment_id.id),
                ('move_line_id', '=', aml_id and aml_id[0].id),
                ('invoice_id', '=', invoice.id)])
            if not inv_pay_log_id:
                invoice.write({'payment_log_ids': [
                    (0, 0, {'payment_id': aml_id and
                            aml_id[0].payment_id.id or False,
                            'amount': amount,
                            'move_line_id': aml_id and aml_id[0].id,
                            'date': date.today()})]})
        return res
