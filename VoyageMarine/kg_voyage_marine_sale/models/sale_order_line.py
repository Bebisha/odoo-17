from collections import defaultdict
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, format_date


class KGSaleOrderLineInherit(models.Model):
    _inherit = "sale.order.line"

    labour_cost_id = fields.Many2one("crm.labour.cost", string="Labour Id")
    amount_in_currency = fields.Float(string="Amount in Currency(AED)", compute="convert_amount_in_currency")
    qtn_line_id = fields.Many2one("sale.qtn.line", string="QTN Line", copy=False)
    qtn_line_ids = fields.Many2many("sale.qtn.line", string="QTN Lines", copy=False)

    is_product_select = fields.Boolean(string="Select",
                                       help="To Select products from order line",
                                       copy=False, default=True)
    is_inv_select = fields.Boolean(string="Select",
                                   help="To Select invoice products from order line",
                                   copy=False, default=True)
    line_readonly = fields.Boolean(default=False, string="Line Readonly", copy=False)
    available_reserved_lots = fields.Boolean()
    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'),('ft','FT')
    ], string="Code")

    is_items = fields.Boolean(string="Is Items", default=False)
    is_labour = fields.Boolean(string="Is Items", default=False)
    is_other = fields.Boolean(string="Is Items", default=False)
    is_material = fields.Boolean(string="Is Items", default=False)
    is_fl = fields.Boolean(string="is_fl", default=False, copy=False)
    material_cost_id = fields.Many2one('crm.material.cost', string="Material Cost")
    other_cost_id = fields.Many2one('crm.other.cost', string="Other Cost")
    item_id = fields.Many2one('crm.estimation.item', string="Items")
    labour_id = fields.Many2one("crm.labour.cost", string="Labour Id")
    is_add = fields.Boolean(default=False,copy=False)
    parent_line_id = fields.Many2one('sale.order.line', string='Parent Line')
    child_line_ids = fields.One2many('sale.order.line','parent_line_id',column1='sub_sale_order_line', string='Sub Items')
    is_order_approved = fields.Boolean(
        related='order_id.qtn_requested_approved',
        store=False
    )

    _sql_constraints = [
        ('accountable_required_fields',
         "CHECK(1=1)",
         "Missing required fields on accountable sale order line."),
        ('non_accountable_null_fields',
         "CHECK(1=1)",
         "Forbidden values on non-accountable sale order line"),
    ]

    sl_no = fields.Char(string="Sl.No", readonly=False)

    kg_description = fields.Html(string="Description")
    previous_sol_id = fields.Many2one("sale.order.line", string="Previous ID", copy=False)

    delivery_date = fields.Date(string="Delivery Date")

    copy_delivered_qty = fields.Float(string="Copy Delivered Qty", copy=False)
    # is_sub_item = fields.Boolean(string="sub")
    is_subitem = fields.Boolean(default=False)
    main_line_id = fields.Many2one('sale.order.line', compute="compute_parent_line")
    manin_product_order_line_id = fields.Many2one('sale.order.line')
    main_line_sl = fields.Integer('Main Line SL')
    sub_item_price = fields.Float(string="Subitem Unit Price", force_save=True, store=True)
    is_bom = fields.Boolean(string="IS Bom", copy=False)
    margin_per = fields.Float(string="Margin %")
    unit_price_margin_incl = fields.Float(string="Unit Price(Margin Incl)", compute="_price_with_margin")
    fixed_discount = fields.Float(string="Disc. Amount", digits="Product Price", default=0.000)

    is_discount_line = fields.Boolean(string='Is Discount Line', compute='_compute_is_discount_line', store=True)
    # is_rental_product = fields.Boolean(string="Is Rental Product", default=False)
    delivery_schedule = fields.Char(
        string="Delivery Schedule"
    )

    def _prepare_invoice_line(self, **optional_values):
        """ Inherited to pass code from sale order line to journal item """
        res = super()._prepare_invoice_line(**optional_values)
        if self.margin_per:
            res['price_unit'] = self.unit_price_margin_incl

        res.update({
            'code': self.code,
            'division_id': self.order_id.division_id.id,

        })
        # if self.processing_doc_ids:
        #     res['inv_attachment_ids'] = [(6, 0, self.processing_doc_ids.ids)]
        return res
    #
    # @api.onchange('order_line', 'sub_item_price')
    # def _onchange_sub_item_price_update_unit(self):
    #     for line in self:
    #         print("jjjjjjjjjjjjjjjjjjj")
    #         if line.main_line_id:
    #             continue
    #
    #         sub_lines = line.filtered(
    #             lambda l: l.main_line_id.id == line.id
    #         )
    #         print(sub_lines, "sub_linessub_lines")
    #
    #         sub_total = sum(sub_lines.mapped('price_subtotal'))
    #
    #         if line.product_uom_qty:
    #             line.price_unit = line.base_price_unit + (sub_total / line.product_uom_qty)
    #         else:
    #             line.price_unit = line.base_price_unit

    @api.onchange('margin_per', 'price_unit')
    @api.depends('margin_per', 'price_unit')
    def _price_with_margin(self):
        for rec in self:
            if rec.margin_per and rec.price_unit:
                margin_amount = rec.price_unit * (rec.margin_per / 100)
                rec.unit_price_margin_incl = rec.price_unit + margin_amount
            else:
                rec.unit_price_margin_incl = rec.price_unit or 0.0

    # @api.onchange('sub_item_price', 'price_unit')
    # @api.depends('sub_item_price', 'price_unit')
    # def _price_with_sub_item_price(self):
    #     for rec in self:
    #         print("kkkkkkkkkk")
    #         if rec.sub_item_price and rec.price_unit:
    #             print("rec.price_unit",rec.price_unit)
    #             amount = rec.price_unit + rec.sub_item_price
    #             rec.unit_price = amount
    #         else:
    #             rec.unit_price = 0.0

    @api.depends('product_id.is_discount_product', 'display_type')
    def _compute_is_discount_line(self):
        for line in self:
            line.is_discount_line = bool(
                line.product_id and
                line.product_id.is_discount_product or
                line.display_type
            )

    @api.onchange('main_line_sl')
    @api.depends('main_line_sl')
    def compute_parent_line(self):
        for rec in self:
            rec.main_line_id = False
            if rec.main_line_sl:
                parent_line = rec.order_id.order_line.filtered(lambda x: x.sl_no == str(rec.main_line_sl))
                if parent_line:
                    rec.main_line_id = parent_line[0].id



    @api.onchange("discount",'product_uom_qty','price_unit')
    def _onchange_discount(self):
        for line in self:
            if line.discount != 0:
                line.fixed_discount = 0.0
                margin_amount = (line.price_unit * line.product_uom_qty) * (line.margin_per / 100.0)
                fixed_discount = ((line.price_unit * line.product_uom_qty) + margin_amount) * (line.discount / 100.0)
                line.update({"fixed_discount": fixed_discount})
            if line.discount == 0:
                fixed_discount = 0.000
                line.update({"fixed_discount": fixed_discount})
            line._compute_amount()

    @api.onchange("fixed_discount")
    def _onchange_fixed_discount(self):
        for line in self:
            if line.fixed_discount != 0:
                line.discount = 0.0
                margin_amount = (line.price_unit * line.product_uom_qty) * (line.margin_per / 100.0)
                discount = (((line.product_uom_qty * line.price_unit) + margin_amount) - (((line.product_uom_qty * line.price_unit) + margin_amount) - line.fixed_discount)) / ((line.product_uom_qty * line.price_unit) + margin_amount) * 100 or 0.0
                line.update({"discount": discount})
            if line.fixed_discount == 0:
                discount = 0.0
                line.update({"discount": discount})
            line._compute_amount()

    @api.depends('price_subtotal', 'product_uom_qty', 'purchase_price','margin_per')
    def _compute_margin(self):
        for line in self:
            line.margin = (line.price_unit * line.product_uom_qty) * (line.margin_per / 100.0)
            line.margin_percent = line.margin

    # @api.onchange('margin_per')
    # def onchange_margin_per(self):
    #     for line in self:
    #         line.price_unit = line.margin_per * line.purchase_price

    def _effective_price_unit_with_margin(self):
        self.ensure_one()
        qty = self.product_uom_qty or 0.0
        fixed_disc = getattr(self, 'fixed_discount', 0.0) or 0.0
        margin = (self.margin_per or 0.0) / 100.0
        unit = self.price_unit
        unit *= (1.0 + margin)
        unit -= (fixed_disc / qty) if qty else fixed_disc

        return unit

    def _convert_to_tax_base_line_dict(self, **kwargs):
        res = super()._convert_to_tax_base_line_dict()
        res.update({
            'price_unit': self._effective_price_unit_with_margin(),
            'discount': 0.0,
        })
        return res

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'margin_per', 'fixed_discount')
    def _compute_amount(self):
        return super()._compute_amount()

    def _check_price_against_cost(self, price_unit, product_id, is_subitem):
        """Helper function to check if the price unit is lower than the product's standard price."""
        # Ensure both values exist and are numeric before comparison
        list_price = product_id.list_price or 0.0
        price_unit = price_unit or 0.0

        if (price_unit != 0 and list_price != 0 and price_unit < list_price) and not is_subitem:
            raise ValidationError(
                "Selling Price cannot be less than Product Price.\n"
                "Product Selling Price is %.2f %s\n"
                "If you want to update the sale price and continue, please ensure the change is authorized."
                % (list_price, product_id.currency_id.symbol or '')
            )

    def write(self, vals):
        if vals.get('is_subitem'):
            vals['price_unit'] = 0.0
        if 'price_unit' in vals or 'product_id' in vals:
            price_unit = vals.get('price_unit', self.price_unit)
            product_id = vals.get('product_id', self.product_id.id)
            is_subitem = vals.get('is_subitem', self.is_subitem)

            # Fetch the product object (if it's being updated)
            product_id = self.env['product.product'].browse(product_id)

            # Perform validation
            self._check_price_against_cost(price_unit, product_id, is_subitem)
        # if vals.get('is_subitem', self.is_subitem):
        #     vals['price_unit'] = 0.00

        for line in self:
            is_subitem = vals.get('is_subitem', line.is_subitem)
            if is_subitem:
                vals['price_unit'] = 0
                main_line_id = vals.get('main_line_id', line.main_line_id.id)
                if main_line_id:
                    main_line = self.env['sale.order.line'].browse(main_line_id)
                    code = vals.get('code', line.code)
                    if main_line.is_fl:
                        vals['is_fl'] = False
                    else:
                        vals['is_fl'] = (code == 'fl')


        return super(KGSaleOrderLineInherit, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('code') == 'fl' and not vals.get('is_subitem'):
            vals['is_fl'] = True
        if vals.get('is_subitem'):
            vals['price_unit'] = 0.0
        product_id = self.env['product.product'].browse(vals.get('product_id'))
        price_unit = vals.get('price_unit')
        is_subitem = vals.get('is_subitem', False)

        # Perform validation
        self._check_price_against_cost(price_unit, product_id, is_subitem)


        return super().create(vals)

    def create_subitem(self):
        is_fl_main_item = self.code == 'fl'

        if is_fl_main_item:
            self.is_fl = True

        bom = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)
        ], limit=1, order='id asc')

        code_list = ['sm', 'fm', 'lm', 'nm', 'cm', 'rm', 'pm', 'om', 'mm', 'em']
        if bom and self.code in code_list:
            for line in bom.bom_line_ids:
                print(line.product_id, line.product_qty, "sub_item details")
                existing = self.env["sale.order.line"].search([
                    ('main_line_id', '=', self.id),
                    ('product_id', '=', line.product_id.id),
                    ('is_bom', '=', True)
                ], limit=1)
                if not existing:
                    for idx, bom_line in enumerate(bom.bom_line_ids, start=1):
                        sl_no = f"{self.sl_no}.{idx}"
                        self.env['sale.order.line'].create({
                            'code':bom_line.code if bom_line.code else '',
                            'sl_no': sl_no,
                            'main_line_sl': self.sl_no,
                            'is_subitem': True,
                            'order_id': self.order_id.id,
                            'product_id': bom_line.product_id.id,
                            'name': bom_line.product_id.display_name,
                            'product_uom_qty': bom_line.product_qty,
                            'product_uom': bom_line.product_uom_id.id,
                            'price_unit': 0.00,
                            'sequence': self.sequence + idx,
                            'is_product_select': False,
                            'is_inv_select': False,
                            'is_bom': True,
                        })
        sub_lines = self.order_id.order_line.filtered(lambda x: x.main_line_id.id == self.id)
        print(sub_lines,"sub_lines")
        if not self.base_price_unit:

            self.write({
                'base_price_unit': self.price_unit
            })
        print(self.main_line_id,"self.main_line_id")
        sl_no = f"{self.sl_no}.{len(sub_lines) + 1}"
        self.env['sale.order.line'].create({
            'sl_no': sl_no,
            'main_line_sl': self.sl_no,
            # 'main_line_id': self.id,
            'is_subitem': True,
            'order_id': self.order_id.id,
            'name': '',
            'price_unit':0,
            'is_product_select': False,
            'is_inv_select': False,
            'sequence': self.sequence + len(sub_lines) + 1,
        })
    # chechi tell to comment the function
    # def unlink(self):
    #     SaleOrderLine = self.env['sale.order.line']
    #     for line in self:
    #         if not line.is_subitem:
    #             subitems = SaleOrderLine.search([('main_line_id', '=', line.id), ('is_subitem', '=', True)])
    #             if subitems:
    #                 raise ValidationError(_("You must delete all subitems before deleting the main item."))
    #         if line.is_subitem and line.main_line_id:
    #             related_lines = SaleOrderLine.search([
    #                 ('main_line_id', '=', line.main_line_id.id),
    #                 ('is_subitem', '=', True)
    #             ])
    #             remaining_lines = related_lines.filtered(lambda l: l.id != line.id)
    #             for idx, sline in enumerate(remaining_lines, start=1):
    #                 sline.sl_no = f"{line.main_line_id.sl_no}.{idx}"
    #         if line.qtn_line_ids:
    #             raise ValidationError(_("You cannot delete this line because it is linked to a quotation line!"))
    #
    #         # Uncomment if estimation protection is needed
    #         # if line.order_id and line.order_id.estimation_id:
    #         #     raise ValidationError(
    #         #         _("If a quotation is generated through an estimation, it can't be deleted. Cancel the estimation and create a new one instead."))
    #
    #     return super(KGSaleOrderLineInherit, self).unlink()

    # def unlink(self):
    #     SaleOrderLine = self.env['sale.order.line']
    #     for line in self:
    #         related_lines = SaleOrderLine.search([('main_line_id', '=', line.main_line_id.id)])
    #         if line.is_subitem:
    #             remaining_lines = related_lines.filtered(lambda l: l.id != line.id)
    #             for idx, sline in enumerate(remaining_lines, start=1):
    #                 sline.sl_no = f"{line.main_line_id.sl_no}.{idx}"
    #     if self.qtn_line_ids:
    #         raise ValidationError(_("You can not delete a Quotation lines !!"))
    #     # if self.order_id and self.order_id.estimation_id:
    #     #     raise ValidationError(
    #     #         _("If a quotation is generated through an estimation; it can't be delete the order lines, if there are any changes, cancel the estimation and proceed with a new estimation."))
    #     return super(KGSaleOrderLineInherit, self).unlink()

    @api.onchange('is_jobsheet')
    def hide_create_do(self):
        for rec in self:
            if rec.is_jobsheet:
                rec.is_product_select = False
            else:
                rec.is_product_select = True

    @api.onchange('name')
    def change_section_name(self):
        for rec in self:
            if rec.display_type == 'line_section':
                rec.kg_description = rec.name

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.is_subitem:
                rec.price_unit = 0.00

    base_price_unit = fields.Float(string="Unit Price",copy=False)

    @api.onchange('price_unit')
    def check_product_price(self):
        for rec in self:
            if rec.base_price_unit:
                rec.base_price_unit = rec.price_unit

            if rec.product_id.currency_id != rec.currency_id:
                price_in_product_currency = rec.currency_id._convert(
                    rec.price_unit, rec.product_id.currency_id, rec.company_id, rec.order_id.date_order.date()
                )
            else:
                price_in_product_currency = rec.price_unit

            if price_in_product_currency and price_in_product_currency < rec.product_id.list_price  and not rec.is_subitem and not rec.product_id.is_discount_product:
                raise ValidationError(
                    "Selling Price cannot be less than Product Cost.\n\t Product Cost is %.2f %s" % (
                        rec.product_id.list_price, rec.product_id.currency_id.name))

    @api.onchange('order_id.order_line', 'is_product_select', 'product_id')
    def _get_line_numbers(self):
        for line in self:
            line_num = 1
            for line_rec in line.order_id.order_line:
                if not line_rec.sl_no:
                    if line_rec.is_product_select and line_rec.product_id:
                        line_rec.sl_no = str(line_num)
                        line_num += 1
                    else:
                        line_rec.sl_no = False
                else:
                    current_value = line_rec.sl_no
                    if current_value.isdigit():
                        line_num = max(line_num, int(current_value) + 1)
                    else:
                        if current_value.isalpha():
                            line_rec.sl_no = self._increment_alpha(current_value)

    def _increment_alpha(self, value):
        if value == 'Z':
            return 'AA'
        else:
            return chr(ord(value) + 1)

    @api.onchange('product_uom_qty', 'price_unit', 'tax_id', 'product_uom')
    def restrict_lines(self):
        for rec in self:
            if rec.order_id and rec.order_id.estimation_id and not rec.is_items and not rec.display_type and not rec.is_add:
                raise ValidationError(
                    _("If a quotation is generated through an estimation; it can't be revised with order lines, if there are any changes, cancel the estimation and proceed with a new estimation."))
    """Compute Name Testing Purpose"""
    @api.depends('product_id')

    def _compute_name(self):
        for rec in self:
            if rec.name and rec.product_id and rec.order_id and rec.order_id.qtn_requested:
                if rec.name:
                    rec.name = rec.name
                if rec.product_uom_qty:
                    rec.product_uom_qty = rec.product_uom_qty
                if rec.price_unit:
                    rec.price_unit = rec.price_unit
            elif rec.order_id.estimation_id or rec.order_id.opportunity_id:
                rec.name = f"{rec.name}"
            else:
                return super(KGSaleOrderLineInherit, self)._compute_name()

    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        lines_by_company = defaultdict(lambda: self.env['sale.order.line'])
        cached_taxes = {}
        for line in self:
            lines_by_company[line.company_id] += line

        for company, lines in lines_by_company.items():
            for line in lines.with_company(company):
                if line.order_id and line.order_id.estimation_id:
                    if not line.tax_id:
                        line.tax_id = False
                elif line.order_id.estimation_id and line.is_subitem:
                    line.tax_id = False
                elif line.inspection_calibration_id:
                    default_tax = self.env.company.account_sale_tax_id
                    print(default_tax.name, "default_tax")
                    line.tax_id = default_tax
                else:
                    taxes = None
                    if line.product_id:
                        taxes = line.product_id.taxes_id._filter_taxes_by_company(company)

                    if not line.product_id or not taxes:
                        line.tax_id = False
                        continue

                    fiscal_position = line.order_id.fiscal_position_id
                    cache_key = (fiscal_position.id, company.id, tuple(taxes.ids))
                    cache_key += line._get_custom_compute_tax_cache_key()
                    if cache_key in cached_taxes:
                        result = cached_taxes[cache_key]
                    else:
                        result = fiscal_position.map_tax(taxes)
                        cached_taxes[cache_key] = result
                    line.tax_id = result

    def _timesheet_create_task_prepare_values(self, project):
        res = super(KGSaleOrderLineInherit, self)._timesheet_create_task_prepare_values(project)
        project.enquiry_id = self.order_id.opportunity_id.id
        project.labour_cost_id = self.labour_cost_id.id
        return res

    # def unlink(self):
    #     if self.qtn_line_ids:
    #         raise ValidationError(_("You can not delete a Quotation lines !!"))
    #     # if self.order_id and self.order_id.estimation_id:
    #     #     raise ValidationError(
    #     #         _("If a quotation is generated through an estimation; it can't be delete the order lines, if there are any changes, cancel the estimation and proceed with a new estimation."))
    #     return super(KGSaleOrderLineInherit, self).unlink()

    def convert_amount_in_currency(self):
        for rec in self:
            if rec.price_subtotal and rec.currency_id and rec.order_id.date_order:
                if rec.currency_id != self.env.company.currency_id:
                    converted_amount = rec.currency_id._convert(
                        rec.price_subtotal, self.env.company.currency_id, self.env.company,
                        rec.order_id.date_order.date()
                    )
                    rec.amount_in_currency = converted_amount
                else:
                    rec.amount_in_currency = rec.price_subtotal
            else:
                rec.amount_in_currency = rec.price_subtotal

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields generated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        if self._context.get("skip_procurement"):
            return True
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            if line.is_product_select == False:
                continue
            line = line.with_company(line.company_id)
            if line.state != 'sale' or line.order_id.locked or not line.product_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
                continue
            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:

                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(line._create_procurement(product_qty, procurement_uom, values))
        if procurements:
            self.env['procurement.group'].run(procurements)

        # This next block is currently needed only because the scheduler trigger is done by picking confirmation rather than stock.move confirmation
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])
            if pickings_to_confirm:
                # Trigger the Scheduler for Pickings
                pickings_to_confirm.action_confirm()
        return True

    #
    # def _timesheet_service_generation(self):
    #     for line in self:
    #         if line.is_fl and line.code == 'fl':
    #             result = super()._timesheet_service_generation()
    #             print(result, "result")
    #             return result
    #
    #     return False
    def _timesheet_service_generation(self):
        """ For service lines, create the task or the project. If already exists, it simply links
            the existing one to the line.
            Note: If the SO was confirmed, cancelled, set to draft then confirmed, avoid creating a
            new project/task. This explains the searches on 'sale_line_id' on project/task. This also
            implied if so line of generated task has been modified, we may regenerate it.
        """
        so_line_task_global_project = self.filtered(
            lambda sol: sol.is_service and sol.product_id.service_tracking == 'task_global_project'
        )

        so_line_new_project = self.filtered(
            lambda sol: sol.is_service and sol.is_fl and
                        sol.product_id.service_tracking in ['project_only', 'task_in_project']
        )

        # ---------------------------------------------------------
        # 2️⃣ MAP EXISTING PROJECTS PER SO
        # ---------------------------------------------------------
        map_so_project = {}
        map_so_project_templates = {}

        if so_line_new_project:
            order_ids = self.mapped('order_id').ids

            so_lines_with_project = self.search([
                ('order_id', 'in', order_ids),
                ('project_id', '!=', False),
                ('product_id.service_tracking', 'in', ['project_only', 'task_in_project']),
                ('product_id.project_template_id', '=', False),
            ])
            map_so_project = {sol.order_id.id: sol.project_id for sol in so_lines_with_project}

            so_lines_with_project_templates = self.search([
                ('order_id', 'in', order_ids),
                ('project_id', '!=', False),
                ('product_id.service_tracking', 'in', ['project_only', 'task_in_project']),
                ('product_id.project_template_id', '!=', False),
            ])
            map_so_project_templates = {
                (sol.order_id.id, sol.product_id.project_template_id.id): sol.project_id
                for sol in so_lines_with_project_templates
            }

        # ---------------------------------------------------------
        # 3️⃣ GLOBAL PROJECT TASK CREATION
        # ---------------------------------------------------------
        map_sol_project = {}
        if so_line_task_global_project:
            map_sol_project = {
                sol.id: sol.product_id.with_company(sol.company_id).project_id
                for sol in so_line_task_global_project
            }

        # ---------------------------------------------------------
        # HELPERS
        # ---------------------------------------------------------
        def _can_create_project(sol):
            if not sol.project_id:
                if sol.product_id.project_template_id:
                    return (sol.order_id.id, sol.product_id.project_template_id.id) not in map_so_project_templates
                return sol.order_id.id not in map_so_project
            return False

        def _determine_project(sol):
            if sol.product_id.service_tracking == 'project_only':
                return sol.project_id
            if sol.product_id.service_tracking == 'task_in_project':
                return sol.order_id.project_id or sol.project_id
            return False

        # ---------------------------------------------------------
        # 4️⃣ CREATE PROJECTS + PARENT TASKS FIRST
        # ---------------------------------------------------------
        for so_line in so_line_new_project:
            project = _determine_project(so_line)

            if not project and _can_create_project(so_line):
                project = so_line._timesheet_create_project()
                if so_line.product_id.project_template_id:
                    map_so_project_templates[
                        (so_line.order_id.id, so_line.product_id.project_template_id.id)
                    ] = project
                else:
                    map_so_project[so_line.order_id.id] = project

            elif not project:
                so_line.project_id = (
                        map_so_project_templates.get(
                            (so_line.order_id.id, so_line.product_id.project_template_id.id)
                        ) or map_so_project.get(so_line.order_id.id)
                )
                project = so_line.project_id

            # 🔹 CREATE PARENT TASK
            if so_line.product_id.service_tracking == 'task_in_project':
                if project and not so_line.task_id:
                    so_line._timesheet_create_task(project=project)

            so_line._generate_milestone()

        # ---------------------------------------------------------
        # 5️⃣ GLOBAL PROJECT TASKS
        # ---------------------------------------------------------
        for so_line in so_line_task_global_project:
            if not so_line.task_id and map_sol_project.get(so_line.id) and so_line.product_uom_qty > 0:
                so_line._timesheet_create_task(project=map_sol_project[so_line.id])

        # ---------------------------------------------------------
        # 6️⃣ SUBITEM → SUBTASK CREATION (SAFE)
        # ---------------------------------------------------------
        so_lines_with_subitem_project = self.filtered(
            lambda sol: sol.is_service and sol.is_subitem and sol.code == 'ft' and
                        sol.product_id.service_tracking in ['project_only', 'task_in_project']
        )

        for line in so_lines_with_subitem_project:
            parent_line = line.main_line_id
            if not parent_line:
                continue

            # 🔹 ENSURE PARENT TASK EXISTS
            if not parent_line.task_id:
                project = _determine_project(parent_line)
                if project:
                    parent_line._timesheet_create_task(project=project)

            parent_task = parent_line.task_id
            if not parent_task:
                continue  # safety

            # if line.code == 'ft' and line.product_uom.name == 'Day':
            #     allocated_hours = line.product_uom_qty * 10
            # else:
            #     allocated_hours = 0.00

            # 🔹 CREATE SUBTASK
            sub_task = self.env['project.task'].create({
                'name': f"{line.name}",
                'project_id': parent_task.project_id.id,
                'parent_id': parent_task.id,
                'sale_line_id': line.id,
                'partner_id': line.order_id.partner_id.id,
                'allocated_hours': line.product_uom_qty * 10 if line.product_uom.name == 'Days' else 0.0,
            })

            line.task_id = sub_task
            parent_task.allocated_hours = sum(
                parent_task.child_ids.mapped('allocated_hours')
            )




