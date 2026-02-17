# -*- coding: utf-8 -*-
import base64

from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    delivery_term = fields.Char(string='Delivery Terms')
    country_origin = fields.Many2one('res.country', string='Country of Origin')
    country_supply = fields.Many2one('res.country', string='Country of Supply')
    place_loading = fields.Many2one('res.country', string='Place of Loading')
    place_of_loading = fields.Char(string='Place of Loading')
    delivery_terms_id = fields.Many2one("delivery.terms", string="Delivery Terms")
    batch_id = fields.Many2one("stock.batch", string="Batch")
    batch_info = fields.Char(string="Batch Info", copy=False)

    bank_ids = fields.Many2many("res.partner.bank", string="Banks", compute="compute_bank_ids")

    is_approved = fields.Boolean(default=False, copy=False, string="Approved")
    is_rejected = fields.Boolean(default=False, copy=False, string="Rejected")
    reject_reason = fields.Char(string="Rejected Reason", copy=False)
    currency_omr = fields.Many2one('res.currency', string='Currency OMR', copy=False, compute='compute_currency_omr')

    def compute_currency_omr(self):
        for rec in self:
            rec.currency_omr = self.env['res.currency'].search([('name', '=', 'OMR')], limit=1)

    def compute_bank_ids(self):
        for rec in self:
            rec.bank_ids = False
            if rec.company_id and rec.company_id.bank_ids and rec.currency_id:
                bank_ids = self.company_id.bank_ids.filtered(lambda x: x.currency_id.id == rec.currency_id.id)
                if bank_ids:
                    rec.bank_ids = bank_ids.ids

    @api.onchange('batch_id')
    def get_batch_name(self):
        for rec in self:
            if rec.batch_id:
                rec.batch_info = rec.batch_id.name
            else:
                rec.batch_info = False

    def action_confirm(self):
        """ To add the condition to update price of the product as the last selling price """
        res = super(SaleOrder, self).action_confirm()
        for line in self.order_line:
            line.product_id.write({
                'lst_price': line.price_unit,
            })
            line.product_template_id.write({
                'list_price': line.price_unit,
            })
        return res

    @api.depends('user_id', 'company_id', 'vessel_id')
    def _compute_warehouse_id(self):
        for order in self:
            default_warehouse_id = self.env['ir.default'].with_company(
                order.company_id.id)._get_model_defaults('sale.order').get('warehouse_id')
            if order.state in ['draft', 'sent'] or not order.ids:
                # Should expect empty
                if default_warehouse_id is not None:
                    order.warehouse_id = default_warehouse_id
                else:
                    order.warehouse_id = order.user_id.with_company(order.company_id.id)._get_default_warehouse_id()
            if order.vessel_id and order.vessel_id.warehouse_id:
                order.warehouse_id = order.vessel_id.warehouse_id

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        res['batch_info'] = self.batch_info
        return res

    def action_quotation_send(self):
        res = super(SaleOrder, self).action_quotation_send()
        if self.env.context.get('proforma'):
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf("sale.action_report_pro_forma_invoice",
                                                                            [self.id])
            file_name = str('PRO-FORMA-') + str(self.name)
        else:
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf("sale.action_report_saleorder", [self.id])
            file_name = str('Order-') + str(self.name)

        if isinstance(pdf_content, bytes):
            encoded_pdf = base64.b64encode(pdf_content)

            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'type': 'binary',
                'datas': encoded_pdf.decode(),
                'res_model': 'sale.order',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })

            if 'context' in res:
                res['context']['default_attachment_ids'] = [(4, attachment.id)]

            else:
                res['context'] = {'default_attachment_ids': [(4, attachment.id)]}

        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    vessel_id = fields.Many2one('sponsor.sponsor', related='order_id.vessel_id', string='Vessel', store=True)
    weight = fields.Float(string='Tons', compute='_compute_total_weight', copy=False, digits=(16, 3))
    default_code = fields.Char(string='Code', related='product_template_id.default_code', store=True)
    batch_id = fields.Many2one("stock.batch", string="Batch", related="order_id.batch_id")

    def _convert_to_tax_base_line_dict(self, **kwargs):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.tax_id,
            price_unit=self.price_unit,
            quantity=self.weight,
            discount=self.discount,
            price_subtotal=self.price_subtotal,
            **kwargs,
        )

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            tax_results = self.env['account.tax'].with_company(line.company_id)._compute_taxes([
                line._convert_to_tax_base_line_dict()
            ])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })

    @api.depends('product_uom_qty', 'product_uom')
    def _compute_total_weight(self):
        """ To compute weights in metric tons """
        for line in self:
            weight = (line.product_uom_qty * line.product_uom.factor_inv) / 1000
            line.weight = weight
