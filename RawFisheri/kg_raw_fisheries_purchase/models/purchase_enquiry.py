from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseEnquiry(models.Model):
    _name = "purchase.enquiry"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Purchase Enquiry"

    name = fields.Char(string="Name", copy=False, readonly=True, index=True, default="/")
    order_no = fields.Char("Order No", tracking=True)
    path = fields.Text("Path")
    acc_no = fields.Char(string="Account No", tracking=True)
    order_date = fields.Date(string="Order Date", default=fields.Date.context_today, tracking=True)
    prepared_user = fields.Char(string="Prepared By")
    page_pic = fields.Char(string="Page/Pic", tracking=True)
    enquiry_type_id = fields.Many2one("purchase.enquiry.type", string="Type", tracking=True)
    serial_no = fields.Char(string="Serial No", tracking=True)
    note = fields.Text(string="Note")
    po_enquiry_line_ids = fields.One2many("purchase.enquiry.line", "purchase_enquiry_id", string="Enquiry Lines",
                                          copy=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('send_requested', 'Send Requested'), ('partial_po_created', 'Partial PO Created'),
         ('po_entry_created', 'PO Created'),
         ('cancel', 'Cancelled')], string="State",
        default='draft', copy=False, tracking=True)
    po_create_user_id = fields.Many2one('res.users', string="PO Create User")

    po_entry_ids = fields.Many2many("purchase.entry", 'purchase_enquiry_id', string="Purchase Entries", copy=False)
    entry_count = fields.Integer(string="Entry Count", compute="compute_entry_count")

    set_readonly = fields.Boolean(string="Set Readonly", default=False, compute="compute_set_readonly")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)
    vendor_id = fields.Many2one("res.partner", string="Vendor", copy=False)
    date_of_order = fields.Date(string="Date of Order", copy=False)
    tax_ids = fields.Many2many("account.tax", string="VAT", copy=False, domain="[('type_tax_use','=','purchase')]")
    discount = fields.Float(string="Discount %")

    @api.onchange('currency_id')
    def apply_currency(self):
        for rec in self:
            if rec.currency_id and rec.po_enquiry_line_ids:
                rec.po_enquiry_line_ids.write({'currency_id': rec.currency_id.id})

    @api.onchange('vendor_id')
    def apply_vendor(self):
        for rec in self:
            if rec.vendor_id and rec.po_enquiry_line_ids:
                rec.po_enquiry_line_ids.write({'vendor_id': rec.vendor_id.id})

    @api.onchange('date_of_order')
    def apply_date_of_order(self):
        for rec in self:
            if rec.date_of_order and rec.po_enquiry_line_ids:
                rec.po_enquiry_line_ids.write({'date_of_order': rec.date_of_order})

    @api.onchange('tax_ids')
    def apply_tax_ids(self):
        for rec in self:
            if rec.tax_ids and rec.po_enquiry_line_ids:
                rec.po_enquiry_line_ids.write({'tax_ids': [(6, 0, rec.tax_ids.ids)]})

    @api.onchange('discount')
    def apply_discount(self):
        for rec in self:
            if rec.discount and rec.po_enquiry_line_ids:
                rec.po_enquiry_line_ids.write({'discount': rec.discount})

    def compute_set_readonly(self):
        for rec in self:
            rec.set_readonly = False
            if rec.po_create_user_id.id != self.env.user.id:
                rec.set_readonly = True

    def view_po_entries(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'view_mode': 'tree,form',
            'res_model': 'purchase.entry',
            'domain': [('id', 'in', self.po_entry_ids.ids)],
            'context': {'create': False}
        }

    @api.depends('po_entry_ids')
    def compute_entry_count(self):
        for rec in self:
            rec.entry_count = 0
            if rec.po_entry_ids:
                rec.entry_count = len(rec.po_entry_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = self.env["ir.sequence"].next_by_code("po.enquiry.seq") or "/"
        return super().create(vals_list)

    def action_send_request(self):
        if not self.po_create_user_id:
            raise ValidationError("Please select a PO Create User before sending the request !!")
        if not self.po_enquiry_line_ids:
            raise ValidationError("Enquiry lines are empty !!")
        if not self.po_create_user_id.email:
            raise ValidationError(
                f"Configure the email address for users {self.po_create_user_id.name} in the users profile !")

        email_subject = f"PO Creation Request (Ref {self.name})"

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        record_url = f"{base_url}/web#id={self.id}&model=purchase.enquiry&view_type=form"

        email_body = _(
            "<p>Dear {user},</p>"
            "<p>You have been assigned to create a Purchase Order based on the following enquiry:</p>"

            "<table border='1' cellpadding='6' cellspacing='0' "
            "style='border-collapse:collapse; font-size:13px;'>"
            "<tr><th align='left' style='background:#f2f2f2;'>Reference</th><td>{reference}</td></tr>"
            "<tr><th align='left' style='background:#f2f2f2;'>Order No</th><td>{order_no}</td></tr>"
            "<tr><th align='left' style='background:#f2f2f2;'>Order Date</th><td>{order_date}</td></tr>"
            "<tr><th align='left' style='background:#f2f2f2;'>Prepared By</th><td>{prepared_by}</td></tr>"
            "<tr><th align='left' style='background:#f2f2f2;'>Type</th><td>{type}</td></tr>"
            "</table><br/>"

            "<p>Please review the details and proceed with the PO creation at the earliest convenience.</p>"

            "<p>"
            "<a href='{record_url}' style='background-color:#1abc9c;color:white;"
            "padding:10px 15px;text-decoration:none;border-radius:5px;'>"
            "Create PO</a>"
            "</p>"

            "<p>Best Regards,<br/>{requester}</p>"
        ).format(
            user=self.po_create_user_id.name,
            requester=self.env.user.name,
            reference=self.name,
            order_no=self.order_no,
            order_date=self.order_date,
            prepared_by=self.prepared_user,
            type=self.enquiry_type_id.name,
            record_url=record_url,
        )

        mail_values = {
            'subject': email_subject,
            'body_html': email_body,
            'email_to': self.po_create_user_id.email,
            'author_id': self.env.user.partner_id.id,
            'model': 'purchase.enquiry',
            'res_id': self.id,
        }

        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.sudo().send()

        self.state = 'send_requested'

    def action_cancel(self):
        self.state = 'cancel'

    def create_po_entry(self):
        if self.po_create_user_id.id != self.env.user.id:
            raise UserError("You do not have access to create the purchase entry.")

        if not self.po_enquiry_line_ids:
            raise UserError("No enquiry lines to create Purchase Entry.")

        if self.po_enquiry_line_ids and any(not li.vendor_id and li.is_create_po for li in self.po_enquiry_line_ids):
            raise ValidationError("Please select a Vendor before creating the purchase order !!")

        if self.po_enquiry_line_ids and any(
                not li.date_of_order and li.is_create_po for li in self.po_enquiry_line_ids):
            raise ValidationError("Please select a Date Of Order before creating the purchase order !!")

        if self.po_enquiry_line_ids and any(not li.vessel_id and li.is_create_po for li in self.po_enquiry_line_ids):
            raise ValidationError("Please select a Vessel before creating the purchase order !!")

        if self.po_enquiry_line_ids and any(not li.currency_id and li.is_create_po for li in self.po_enquiry_line_ids):
            raise ValidationError("Please select a Currency before creating the purchase order !!")

        grouped_lines = {}
        po_enquiry_line_ids = self.po_enquiry_line_ids.filtered(lambda x: x.is_create_po and not x.po_created)
        if po_enquiry_line_ids:
            for line in po_enquiry_line_ids:
                key = (line.vessel_id.id, line.vendor_id.id, line.date_of_order, line.currency_id.id)
                grouped_lines.setdefault(key, []).append(line)

            created_entries = self.env['purchase.entry']
            if self.po_entry_ids:
                count = self.entry_count
            else:
                count = 0
            for (vessel_id, vendor_id, date_of_order, currency_id), lines in grouped_lines.items():
                entry_vals = {
                    'vessel_id': vessel_id,
                    'vendor_id': vendor_id,
                    'currency_id': currency_id,
                    'date_of_order': date_of_order,
                    'po_create_user_id': self.po_create_user_id.id,
                    'purchase_enquiry_id': self.id,
                    'order_no': self.order_no,
                    'acc_no': self.acc_no,
                    'prepared_user': self.prepared_user,
                    'serial_no': self.serial_no,
                    'page_pic': self.page_pic,
                    'enquiry_type_id': self.enquiry_type_id.id,
                    'path': self.path,
                    'note': self.note,
                    'po_entry_ids': [(0, 0, {
                        'part_no': line.part_no,
                        'description': line.description,
                        'qty': line.qty,
                        'initial_ordered_qty': line.qty,
                        'uom_id': line.uom_id.id,
                        'order_no': line.order_no,
                        'date': line.date,
                        'price': line.price,
                        'currency_id': line.currency_id.id,
                        'po_enquiry_line_id': line.id,
                        'tax_ids': [(6, 0, line.tax_ids.ids)],
                        'discount': line.discount
                    }) for line in lines]
                }
                entry = self.env['purchase.entry'].create(entry_vals)
                count += 1
                entry.name = str(self.name) + '/' + str(count)
                created_entries |= entry

            self.po_entry_ids = [(6, 0, (self.po_entry_ids | created_entries).ids)]

            po_enquiry_line_ids.write({'po_created': True})
            if all(li.po_created for li in self.po_enquiry_line_ids):
                self.state = 'po_entry_created'
            else:
                self.state = 'partial_po_created'

    def action_draft(self):
        self.state = 'draft'

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a purchase enquiry which is not in draft or cancelled state')
        return super(PurchaseEnquiry, self).unlink()


class PurchaseEnquiryLine(models.Model):
    _name = "purchase.enquiry.line"
    _description = "Purchase Enquiry Line"

    name = fields.Char(string="Name")
    purchase_enquiry_id = fields.Many2one("purchase.enquiry", string="Purchase Enquiry")
    part_no = fields.Char(string="Part No")
    description = fields.Char(string="Description")
    qty = fields.Float(string="Quantity")
    uom_id = fields.Many2one("uom.uom", string="Unit")
    order_no = fields.Char(string="Order Number", related="purchase_enquiry_id.order_no")
    date = fields.Date(string="Date", related="purchase_enquiry_id.order_date")
    vessel_id = fields.Many2one("sponsor.sponsor", string="Vessel")
    vendor_id = fields.Many2one("res.partner", string="Vendor", copy=False)
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id)
    price = fields.Monetary(string="Price", currency_field="currency_id", copy=False)
    date_of_order = fields.Date(string="Date of Order", copy=False)
    is_create_po = fields.Boolean(string="Create PO", default=True, copy=False)
    po_created = fields.Boolean(string="Create PO", default=False, copy=False)
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
