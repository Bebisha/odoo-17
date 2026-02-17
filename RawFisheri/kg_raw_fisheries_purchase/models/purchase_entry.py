from markupsafe import Markup

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64


class PurchaseEntry(models.Model):
    _name = "purchase.entry"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Purchase Entry"

    name = fields.Char(string="Name", copy=False)
    order_no = fields.Char("Order No", tracking=True)
    path = fields.Text("Path")
    acc_no = fields.Char(string="Account No", tracking=True)
    prepared_user = fields.Char(string="Prepared By")
    page_pic = fields.Char(string="Page/Pic", tracking=True)
    enquiry_type_id = fields.Many2one("purchase.enquiry.type", string="Type", tracking=True)
    serial_no = fields.Char(string="Serial No", tracking=True)
    note = fields.Text(string="Note")
    po_entry_ids = fields.One2many("purchase.entry.line", "purchase_entry_id", string="Entry Lines")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('approved', 'Approved'), ('rejected', 'Rejected'),
         ('cancel', 'Cancelled')],
        string="State",
        default='draft', copy=False, tracking=True)
    po_create_user_id = fields.Many2one('res.users', string="PO Create User")

    vessel_id = fields.Many2one("sponsor.sponsor", string="Vessel")
    vendor_id = fields.Many2one("res.partner", string="Vendor")
    date_of_order = fields.Date(string="Date of Order")
    ship_to = fields.Text(string="Ship To")
    bill_to = fields.Text(string="Bill To")
    purchase_enquiry_id = fields.Many2one("purchase.enquiry", string="Purchase Enquiry")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)
    purchase_amount = fields.Monetary(string="PO Amount", currency_field="currency_id",
                                      compute="compute_purchase_amount")
    reject_reason = fields.Char(string="Reject Reason", copy=False)
    received_status = fields.Selection([('partial', 'Partial Received'), ('full', 'Received')],
                                       string="Received Status", copy=False, compute="compute_received_status")

    untaxed_amount = fields.Monetary(string="Untaxed Amount", compute="compute_untaxed_amount",
                                     currency_field="currency_id")
    taxed_amount = fields.Monetary(string="Taxed Amount", compute="compute_taxed_amount", currency_field="currency_id")

    @api.depends('po_entry_ids')
    def compute_untaxed_amount(self):
        for rec in self:
            rec.untaxed_amount = 0.00
            if rec.po_entry_ids:
                rec.untaxed_amount = sum(rec.po_entry_ids.mapped('total_tax_excl'))

    @api.depends('po_entry_ids')
    def compute_taxed_amount(self):
        for rec in self:
            rec.taxed_amount = 0.00
            if rec.po_entry_ids:
                rec.taxed_amount = sum(rec.po_entry_ids.mapped('tax_amount'))

    @api.depends('taxed_amount', 'untaxed_amount')
    def compute_purchase_amount(self):
        for rec in self:
            rec.purchase_amount = rec.taxed_amount + rec.untaxed_amount

    @api.depends('po_entry_ids')
    def compute_received_status(self):
        for rec in self:
            rec.received_status = False
            if rec.po_entry_ids:
                if all(li.received_qty and li.received_qty >= li.qty for li in rec.po_entry_ids):
                    rec.received_status = 'full'
                elif any(li.received_qty and li.received_qty <= li.qty for li in rec.po_entry_ids):
                    rec.received_status = 'partial'
                else:
                    rec.received_status = ''

    @api.onchange('currency_id')
    def apply_currency(self):
        for rec in self:
            if rec.currency_id and rec.po_entry_ids:
                rec.po_entry_ids.write({'currency_id': rec.currency_id.id})

    # @api.model_create_multi
    # def create(self, vals):
    #     for i in vals:
    #         i['name'] = self.env['ir.sequence'].next_by_code('po.entry.seq')
    #     return super(PurchaseEntry, self).create(vals)

    def action_cancel(self):
        self.state = 'cancel'

    def action_send_mail(self):
        if not self.vendor_id.email:
            raise ValidationError(
                f"Configure the email address for vendor {self.vendor_id.name} in the vendor profile !")

        amount = f"{self.currency_id.symbol} {'{:,.2f}'.format(self.purchase_amount)}"

        email_subject = f"{self.vendor_id.name} Order (Ref {self.name})"

        email_body = (
            "<p>Dear {vendor},</p>"
            "<p>Here is in a purchase order <b>{reference}</b> amounting in <b>{amount}</b> from {company}.</p>"
            "<p>Please review this purchase order. If all details are correct, kindly approve it; otherwise, reject the order and provide the reason for any inconsistencies.</p>"
            "<p>Best Regards,<br/>{requester}</p>"
        ).format(
            vendor=self.vendor_id.name,
            requester=self.env.user.name,
            reference=self.name,
            amount=amount,
            company=self.company_id.name,
        )

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        view_url = f"{base_url}/purchase/order/{self.id}"

        buttons = f"""
                    <div>
                       <a href="{view_url}" style="padding:10px 15px;background:#4287f5;color:#fff;text-decoration:none;border-radius:5px;font-weight:bold;">View</a>
                    </div>
                  """

        attachment = False

        pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
            "kg_raw_fisheries_purchase.action_report_purchase_entry",
            [self.id])
        if isinstance(pdf_content, bytes):
            encoded_pdf = base64.b64encode(pdf_content)

            attachment = self.env['ir.attachment'].create({
                'name': f'Purchase_Order_{self.name}.pdf',
                'type': 'binary',
                'datas': encoded_pdf.decode(),
                'res_model': 'purchase.entry',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })

        mail_values = {
            'subject': email_subject,
            'body_html': f"<html><body>{email_body}<br/>{buttons}</body></html>",
            'email_from': self.company_id.email,
            'email_to': self.vendor_id.email,
            'author_id': self.env.user.partner_id.id,
            'model': 'purchase.entry',
            'res_id': self.id,
            'attachment_ids': [(4, attachment.id)] if attachment else [],
        }

        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.sudo().send()

        self.message_post(
            body=Markup("""
                <p>Dear {vendor},</p>
                <p>Here is in a purchase order <b>{reference}</b> amounting in <b>{amount}</b> from {company}.</p>
                <p>Please review this purchase order. If all details are correct, kindly approve it; otherwise, reject the order and provide the reason for any inconsistencies.</p>
                <p>Best Regards,<br/>{requester}.</p>
                """.format(
                vendor=self.vendor_id.name,
                reference=self.name,
                amount=f"{self.currency_id.symbol} {'{:,.2f}'.format(self.purchase_amount)}",
                company=self.company_id.name,
                requester=self.env.user.name,
            )),
            subject=f"{self.vendor_id.name} Order (Ref {self.name})",
            message_type="email",
            subtype_xmlid="mail.mt_comment",
        )

    def action_confirm(self):
        self.state = 'confirm'

    def action_draft(self):
        self.state = 'draft'

    def action_approve(self):
        self.state = 'approved'

    def action_reject(self):
        self.state = 'rejected'

    def confirm_po_entry(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'draft':
                    for active_model in active_models:
                        active_model.action_confirm()
                else:
                    raise UserError("Only Draft PO entries can be confirmed !!")
            else:
                raise UserError("States must be same !!")

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a purchase entry which is not in draft or cancelled state')
        return super(PurchaseEntry, self).unlink()


class PurchaseEntryLine(models.Model):
    _name = "purchase.entry.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Purchase Entry Lines"

    name = fields.Char(string="Name")
    purchase_entry_id = fields.Many2one("purchase.entry", string="Purchase Entry")
    part_no = fields.Char(string="Part No")
    description = fields.Char(string="Description")
    qty = fields.Float(string="Quantity")
    received_qty = fields.Float(string="Received")
    initial_ordered_qty = fields.Float(string="Initial Ordered")
    uom_id = fields.Many2one("uom.uom", string="Unit")
    order_no = fields.Char(string="Order Number", related="purchase_entry_id.order_no")
    date = fields.Date(string="Date", related="purchase_entry_id.date_of_order")
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)
    price = fields.Monetary(string="Price", currency_field="currency_id")
    po_enquiry_line_id = fields.Many2one("purchase.enquiry.line", string="Enquiry Line", copy=False)
    total_tax_excl = fields.Monetary(string="VAT excl.", currency_field="currency_id", compute="compute_total_tax_excl")
    total = fields.Monetary(string="Total", currency_field="currency_id", compute="compute_total")
    tax_ids = fields.Many2many("account.tax", string="VAT", copy=False, domain="[('type_tax_use','=','purchase')]")
    discount = fields.Float(string="Disc %")
    tax_amount = fields.Monetary(string="Tax Amount", currency_field="currency_id", compute="compute_tax_amount")

    @api.depends('qty', 'price', 'discount')
    def compute_total_tax_excl(self):
        for rec in self:
            rec.total_tax_excl = 0.00
            if rec.discount:
                amount = rec.qty * rec.price
                rec.total_tax_excl = amount - (amount * (rec.discount / 100))
            else:
                rec.total_tax_excl = rec.qty * rec.price

    @api.depends('total_tax_excl', 'tax_amount')
    def compute_total(self):
        for rec in self:
            rec.total = rec.tax_amount + rec.total_tax_excl

    @api.depends('tax_ids', 'total_tax_excl')
    def compute_tax_amount(self):
        for rec in self:
            rec.tax_amount = 0.00
            if rec.tax_ids:
                value = 0
                for tax in rec.tax_ids:
                    value += rec.total_tax_excl * (tax.amount / 100)
                rec.tax_amount = value
