from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sequence_code = fields.Char(string='Sequence Code', default='AE%(y)s')
    # product_model_id = fields.Many2one('product.model', string='Model', required=True)
    product_model_no = fields.Char( string='Model No.')
    # account_analytic_id = fields.Many2many('account.analytic.account',string='Analytic Account')
    terms_conditions_id = fields.Many2one('custom.terms.conditions', copy=False)
    custom_terms_conditions = fields.Html(related='terms_conditions_id.terms_condition', copy=False)
    asf_date = fields.Date(string='ASF Date')
    rfq_number = fields.Char('Quote No.', copy=False)

    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New' and values.get('state', 'draft') in ('draft', 'sent'):
            values['name'] = self.env['ir.sequence'].next_by_code('rfq') or 'New'
        return super(PurchaseOrder, self).create(values)

    def button_confirm(self):

        for order in self:
            order.rfq_number = order.name
            req_for_quo = self.env['ir.sequence'].next_by_code('rfq_purchase_order')
            update_seq = {'name': req_for_quo}
            order.update(update_seq)
            for rec in order.order_line:
                if rec.product_id:
                    vendor_pricelist_id = self.env['product.supplierinfo'].search(
                        [('partner_id', '=', rec.order_id.partner_id.id),
                         ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id), ('active', '=', True),
                         ])
                    if vendor_pricelist_id:
                        vendor_pricelist_id.price = rec.price_unit
        return super(PurchaseOrder, self).button_confirm()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    account_analytic_ids = fields.Many2many('account.analytic.account', string='Analytic Account')
    brand_id = fields.Many2one('product.brand', related='product_id.brand_id', store=True)


class InheritProductSupplierInfo(models.Model):
    _inherit = "product.supplierinfo"

    active = fields.Boolean(default=True)
    brand_id = fields.Many2one('product.brand', related='product_tmpl_id.brand_id', store=True)
