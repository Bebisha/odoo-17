from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PackageList(models.Model):
    _name = 'package.list'
    _description = 'Package List'

    name = fields.Char(string="Packing Number", copy=False, index=True, readonly=False,
                       default=lambda self: _('New'))
    sale_order_id = fields.Many2one('sale.order', string="Sale Order", required=True)
    partner_id = fields.Many2one('res.partner', string="Shipper")
    consignee_id = fields.Many2one('res.partner', string="Consignee")
    bill_id = fields.Many2one('res.partner', string="Bill to")
    packing_line_ids = fields.One2many('package.line', 'package_id', string="Packing Lines")
    commercial_line_ids = fields.One2many('package.line', 'package_id', string="Commercial Lines")
    invoice_no = fields.Char(string="Invoice No")
    invoice_id= fields.Many2one('account.move',string="Invoice No")
    date = fields.Date(string="Date")
    vessel_name = fields.Char(string="Vessel Name")
    vessel_id = fields.Many2one('vessel.code', string='Vessel')
    project_name = fields.Char(string="Project Name")
    model_of_transport = fields.Char(string="Model of Transport")
    no_of_packages = fields.Integer(string="No. Of Packages")
    total_net_weight = fields.Float(string="Total Net Weight (Kg)")
    total_gross_weight = fields.Float(string="Total Gross Weight (Kg)")
    total_volume = fields.Float(string="Total Volume (CBM)")
    job_no = fields.Char(string="Job No")
    po_ids = fields.Many2many('purchase.order', string="Po No")
    po_reference = fields.Char(string="Po No.")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    packing_form_count = fields.Integer(
        string="Sale Count",
        compute="_compute_form_counts_sale"
    )
    commercial_inv_no = fields.Char(string="Commercial Invoice")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('packing.no') or _('New')

                vals['commercial_inv_no'] = self.env['ir.sequence'].next_by_code('commercial.inv')
        return super().create(vals_list)

    def _compute_form_counts_sale(self):
        for order in self:
            order.packing_form_count = self.env['sale.order'].search_count([('id', '=', self.sale_order_id.id)])

    def action_sale_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', '=', self.sale_order_id.id)],
            'context': {'create': False}
        }

    def action_cipl(self):
        return self.env.ref('kg_voyage_marine_sale.action_cipl').report_action(self.id)

    # @api.onchange('sale_order_id')
    # def _onchange_sale_order_id(self):
    #     if self.sale_order_id:
    #         packing_lines = []
    #         commercial_lines = []
    #
    #         for line in self.sale_order_id.order_line:
    #             if line.product_id.type == 'service':  # Example condition for Commercial
    #                 commercial_lines.append((0, 0, {
    #                     'product_id': line.product_id.id,
    #                     'description': line.name,
    #                     'quantity': line.product_uom_qty,
    #                     'unit_price': line.price_unit,
    #                     'subtotal': line.price_subtotal,
    #                 }))
    #             else:  # Default to Packing
    #                 packing_lines.append((0, 0, {
    #                     'product_id': line.product_id.id,
    #                     'description': line.name,
    #                     'quantity': line.product_uom_qty,
    #                     'unit_price': line.price_unit,
    #                     'subtotal': line.price_subtotal,
    #                 }))
    #         self.packing_line_ids = packing_lines
    #         self.commercial_line_ids = commercial_lines


class PackageLine(models.Model):
    _name = 'package.line'
    _description = 'Package Line'

    package_id = fields.Many2one('package.list', string="Package List", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product")
    product_tempt_id = fields.Many2one('product.template', 'Product')
    product_uom_id = fields.Many2one('uom.uom', string="Product Uom")
    description = fields.Text(string="Description")
    quantity = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Unit Price")
    subtotal = fields.Float(string="Subtotal")
    net_weight_per_unit = fields.Float(string="Net Weight (Kg)")
    dimension_l = fields.Float(string="Dimension Length (cm)")
    dimension_w = fields.Float(string="Dimension Width (cm)")
    dimension_h = fields.Float(string="Dimension Height (cm)")
    gross_weight = fields.Float(string="Gross Weight (Kg)")
    packing_type = fields.Char(string="Packing Type")
    country_of_orgin = fields.Char(string="County of Origin")
    hs_code = fields.Char(string="HS code")
    box_no = fields.Char(string="Box No")
    tag_no = fields.Char(string="TAG No")
    subtotal = fields.Float(string='Subtotal', compute='_compute_total', store=True)

    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for record in self:
            record.subtotal = record.quantity * record.unit_price

    @api.depends('subtotal')
    def _compute_total_amount(self):
        for record in self:
            # Sum all subtotals to get the total amount
            record.total_amount = sum(self.mapped('subtotal'))
