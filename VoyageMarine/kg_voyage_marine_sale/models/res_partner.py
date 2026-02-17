from odoo import models, fields, api


class KGResPartnerInherit(models.Model):
    _inherit = "res.partner"

    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
    ], string="Partner Type")

    po_attach_files = fields.Many2many('ir.attachment', string="Purchase Files")
    is_default_attn = fields.Boolean(default=False, string="Default Att")
    customer_code = fields.Char(string="Customer Code", copy=False)
    vendor_code = fields.Char(string="Vendor Code" ,copy=False)
    fax = fields.Char(string="FAX")
    type_of_company = fields.Char(string="Type of Company")
    trade_license_no = fields.Char(string="Trade License No")
    trade_license_expiry = fields.Date(string="Trade License Expiry")
    signature_documents = fields.Char(string="Signature Documents")
    supplier_category = fields.Many2one("supplier.category", string="Supplier Category")

    @api.model
    def create(self, vals):
        if vals.get('partner_type') == 'customer':
            vals['customer_rank'] = 1
        elif vals.get('partner_type') == 'vendor':
            vals['supplier_rank'] = 1
        res = super(KGResPartnerInherit, self).create(vals)
        if  vals.get('customer_rank') and vals.get('customer_rank') >= 1 :
            vv = res.env['ir.sequence'].next_by_code('customer_code_seq')
            res.customer_code = vv
        if  vals.get('supplier_rank') and vals.get('supplier_rank') >= 1  :
            res.vendor_code = res.env['ir.sequence'].next_by_code('vendor_code_seq')
        return res


class KGResPartnerCategoryInherit(models.Model):
    _inherit = "res.partner.category"

    category_code = fields.Char(string="Code")
