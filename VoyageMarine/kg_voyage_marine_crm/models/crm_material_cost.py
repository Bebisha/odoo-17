from odoo import fields, models, api
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class CrmMaterialCost(models.Model):
    _name = 'crm.material.cost'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "CRM Material Cost"

    material_cost_id = fields.Many2one('crm.estimation')
    product_id = fields.Many2one('product.product', string="Product")
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Qty', default=1)
    uom_id = fields.Many2one('uom.uom', string='UOM')
    unit_price = fields.Float(string='Unit Price')
    total = fields.Float(string='Total', compute='compute_total')
    margin = fields.Float(string='Margin %', readonly=False)
    margin_amount = fields.Float(string='Margin Amount')
    subtotal = fields.Float(string='Subtotal', compute='compute_subtotal')
    currency_id = fields.Many2one("res.currency", related="material_cost_id.currency_id", string="Currency")
    company_id = fields.Many2one("res.company", related="material_cost_id.company_id", string="Company")

    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False, help="Technical field for UX purpose.")

    po_qty = fields.Float(string="PO Qty")
    balance_qty = fields.Float(string="Balance Qty")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])

    main_product_id = fields.Many2one("crm.material.cost", string="Main Product Reference")
    is_sub_item = fields.Boolean(default=False, string="Subitem")
    sub_item_ids = fields.Many2many("crm.material.cost", string="Subitems", compute="compute_subitems", copy=True)

    code = fields.Selection([
        ('ds', 'DS'),
        ('sm', 'SM'),
        ('fs', 'FS'),
        ('fm', 'FM'),
        ('ss', 'SS'),
        ('lm', 'LM'),
        ('ns', 'NS'),
        ('nm', 'NM'),
        ('cs', 'CS'),
        ('cm', 'CM'),
        ('rs', 'RS'),
        ('rm', 'RM'),
        ('ps', 'PS'),
        ('pm', 'PM'),
        ('os', 'OS'),
        ('om', 'OM'),
        ('ms', 'MS'),
        ('mm', 'MM'),
        ('es', 'ES'),
        ('em', 'EM'),('ft','FT'),('fl','FL')
    ], string="Code")


    total_subitems = fields.Float(string="Total Subitems", compute="compute_total_subitems")
    lead_sub_items_ids = fields.Many2many("crm.material.cost", relation='material_sub_items', column1='mater_col1',
                                         column2='materials_col2', string="Subitems", copy=True)
    is_confirm = fields.Boolean(default=False, string="IS confirm", compute="compute_is_confirm")
    is_bom = fields.Boolean(string="IS confirm",copy=False)
    is_bom_remove = fields.Boolean(string="IS confirm",copy=False)

    sl_no = fields.Char(string="Sl.No", readonly=False)

    subitems_total = fields.Float(string="Subitems Total", compute="compute_subitems")
    total_unit_price = fields.Float(string="Total Unit Price", compute="compute_total_unit_price")
    inspection_calibration_id = fields.Many2one('inspection.calibration', string="Inspection")

    def _recompute_parent_margin(self, parent):
        """Recompute main product margin based on the average of all subitem margins."""
        if not parent:
            return
        subitems = parent.sub_item_ids
        if not subitems:
            parent.write({'margin': 0.0, 'margin_amount': 0.0})
            return

        total_margin = sum(subitems.mapped('margin'))
        valid_subitems = parent.sub_item_ids.filtered(
            lambda s: s.margin not in (False, None, 0.0)
        )
        count = len(valid_subitems)
        avg_margin = total_margin / count if count > 0 else 0.0
        total = parent.total_unit_price or 0.0
        margin_amount = total * avg_margin / 100
        print(margin_amount, "margin_amount")
        parent.write({
            'margin': avg_margin,
            'margin_amount': margin_amount,
        })

    def _update_main_unit_price_from_subitems(self):
        for rec in self:
            print(rec, "rec")
            if rec.is_sub_item:
                continue

            subitems = self.env['crm.material.cost'].search([
                ('main_product_id', '=', rec.id)
            ])

            if not subitems:
                continue

            total_sub_qty = sum(subitems.mapped('quantity'))
            total_sub_amount = sum(subitems.mapped('total'))
            print(total_sub_amount, "total_sub_amount")
            if total_sub_qty > 0 and rec.quantity > 0:
                rec.unit_price = total_sub_amount / rec.quantity
            else:
                rec.unit_price = 0.0

    def write(self, vals):
        res = super(CrmMaterialCost, self).write(vals)
        for rec in self:
            if rec.main_product_id:
                rec.main_product_id._update_main_unit_price_from_subitems()
            if not rec.is_sub_item and 'quantity' in vals:
                rec._update_main_unit_price_from_subitems()
        if 'margin' in vals:
            for rec in self:
                if rec.main_product_id:
                    rec._recompute_parent_margin(rec.main_product_id)
        return res

    def create(self, vals_list):
        records = super(CrmMaterialCost, self).create(vals_list)
        for rec in records:
            if rec.main_product_id:
                rec._recompute_parent_margin(rec.main_product_id)
        return records

    @api.onchange('subitems_total', 'quantity')
    def _onchange_update_unit_price_from_subitems(self):
        for rec in self:
            if not rec.is_sub_item:
                rec._update_main_unit_price_from_subitems()


    @api.onchange('margin', 'total')
    def _onchange_margin_percent(self):
        for rec in self:
            if rec.total and rec.margin:
                rec.margin_amount = (rec.total * rec.margin) / 100
            elif not rec.margin:
                rec.margin_amount = 0.0

    # @api.onchange('margin_amount', 'total')
    # def _onchange_margin_amount(self):
    #     for rec in self:
    #         if rec.total:
    #             rec.margin = (rec.margin_amount / rec.total) * 100
    #         elif not rec.margin_amount:
    #             rec.margin = 0.0

    @api.depends('unit_price', 'quantity')
    def compute_total_unit_price(self):
        for rec in self:
            base_total = rec.quantity * rec.unit_price
            rec.total_unit_price = base_total

    @api.onchange('material_cost_id.material_cost_ids', 'code')
    def _get_line_numbers(self):
        for line in self:
            line_num = 1
            for line_rec in line.material_cost_id.material_cost_ids:
                if not line_rec.sl_no:
                    print('11111111111111')
                    if line_rec.code:
                        line_rec.sl_no = str(line_num)
                        line_num += 1

                    else:
                        line_rec.sl_no = False
                else:
                    print('222222222222222222222')
                    current_value = line_rec.sl_no
                    if current_value.isdigit():
                        line_num = max(line_num, int(current_value) + 1)
                    else:
                        if current_value.isalpha():
                            line_rec.sl_no = self._increment_alpha(current_value)



    @api.onchange('unit_price')
    def check_product_price(self):
        for rec in self:

            if rec.product_id.currency_id != rec.currency_id:
                price_in_product_currency = rec.currency_id._convert(
                    rec.unit_price, rec.product_id.currency_id, rec.company_id, rec.material_cost_id.estimate_date
                )
            else:
                price_in_product_currency = rec.unit_price

            if price_in_product_currency and price_in_product_currency < rec.product_id.standard_price and not rec.is_sub_item:
                raise ValidationError(
                    "Selling Price cannot be less than Product Cost.\n\t Product Cost is %.2f %s" % (
                        rec.product_id.lst_price, rec.product_id.currency_id.name))


    # @api.onchange('unit_price')
    # def check_product_price(self):
    #     for rec in self:
    #         if rec.product_id.currency_id != rec.currency_id:
    #             price_in_sale_product_currency = rec.product_id.currency_id._convert(
    #                 rec.product_id.standard_price, rec.currency_id, rec.company_id, rec.material_cost_id.estimate_date
    #             )
    #             if rec.unit_price < price_in_sale_product_currency:
    #                 raise ValidationError(
    #                     "Selling Price cannot be less than Product Cost.\n\t Product Cost is %.2f %s" % (
    #                         rec.product_id.list_price, rec.product_id.currency_id.name))
    #         else:
    #             price_in_product_currency = rec.unit_price
    #             if  price_in_product_currency < rec.product_id.list_price:
    #                 raise ValidationError(
    #                     "Selling Price cannot be less than Product Cost.\n\t Product Cost is %.2f %s" % (
    #                         rec.product_id.list_price, rec.product_id.currency_id.name))

    def _increment_alpha(self, value):
        if value == 'Z':
            return 'AA'
        else:
            return chr(ord(value) + 1)

    def compute_is_confirm(self):
        for rec in self:
            if rec.main_product_id.material_cost_id.status == 'confirm':
                rec.is_confirm=True
            else:
                rec.is_confirm = False

    @api.depends('total')
    def compute_total_subitems(self):
        for rec in self:
            subitems_id = self.env['crm.material.cost'].search([('main_product_id', '=', rec.id)])
            rec.total_subitems = sum(subitems_id.mapped('total')) + rec.total if subitems_id else rec.total

    def kg_add_subitems(self):
        self.ensure_one()

        domain = [('main_product_id', '=', self.id), ('is_bom_remove', '=', False)]
        context = dict(
            default_main_product_id=self.id,
            default_is_sub_item=True,
        )

        bom = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)
        ], limit=1)

        # Allowed codes
        allowed_codes = [
            'ds', 'sm', 'fs', 'fm', 'ss', 'lm', 'ns', 'nm',
            'cs', 'cm', 'rs', 'rm', 'ps', 'pm', 'os', 'om',
            'ms', 'mm', 'es', 'em', 'ft', 'fl'
        ]

        if bom and self.code in allowed_codes and self.material_cost_id.status != 'confirm':

            for line in bom.bom_line_ids:
                product = line.product_id

                existing = self.env["crm.material.cost"].search([
                    ('main_product_id', '=', self.id),
                    ('product_id', '=', product.id),
                    ('is_bom', '=', True),
                ], limit=1)

                if existing and existing.is_bom_remove:
                    continue

                bom_line_code = getattr(line, 'code', '') or ''
                #
                # ❌ INVALID CODE → SHOW WARNING
                if bom_line_code and bom_line_code not in allowed_codes:
                    raise UserError(
                        f"Invalid BOM item code '{bom_line_code}' found in product '{product.name}'.\n"
                        f"Allowed codes: {allowed_codes}"
                    )

                if not existing:
                    self.sub_item_ids = [(0, 0, {
                        'product_id': product.id,
                        'description': product.name,
                        'quantity': line.product_qty,
                        'main_product_id': self.id,
                        'is_bom': True,
                        'code': bom_line_code,
                        'is_bom_remove': False,
                        'unit_price': line.unit_price,
                    })]

        # Context rules
        context['create'] = not (not self.material_cost_id.is_qtn and self.material_cost_id.so_ids)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Costs',
            'view_mode': 'tree',
            'res_model': 'crm.material.cost',
            'domain': domain,
            'context': context,
            'target': 'new'
        }

    def compute_subitems(self):
        for rec in self:
            material_ids = self.search([('main_product_id', '=', rec.id)])
            if material_ids:
                rec.sub_item_ids = [(6, 0, material_ids.ids)]
                rec.subitems_total = sum(material_ids.mapped('subtotal'))
            else:
                rec.sub_item_ids = False
                rec.subitems_total = 0.00

    @api.onchange('product_id')
    def compute_margin(self):
        estimation_margin = self.env['ir.config_parameter'].sudo().get_param('margin', default=False)
        for line in self:
            line.margin = estimation_margin

    @api.depends('total_unit_price', 'margin', 'margin_amount')
    def compute_subtotal(self):
        for line in self:
            if line.margin:
                print("llllll")
                margin = line.margin / 100
                line.subtotal = line.total_unit_price + (line.margin_amount)
            else:
                line.subtotal = line.total_unit_price

    @api.depends(
        'quantity',
        'unit_price',
        'margin',
        'subitems_total',
        'is_sub_item'
    )
    def compute_total(self):
        for line in self:
            base_amount = (line.quantity or 0.0) * (line.unit_price or 0.0)

            # SUBITEM → margin applies
            if line.is_sub_item:
                if line.margin and line.margin > 0:
                    margin_amount = base_amount * line.margin / 100.0
                    line.total = base_amount
                else:
                    line.total = base_amount

            # MAIN ITEM → NO margin, add subitems
            else:
                line.total = base_amount + (line.subitems_total or 0.0)


    @api.onchange('product_id')
    def onchange_product(self):
        for product in self:
            product.description = product.product_id.name
            product.uom_id = product.product_id.uom_id.id
            product.unit_price = product.product_id.lst_price

    def unlink(self):
        for rec in self:
            if rec.is_confirm:
                raise ValidationError("You cannot delete a confirmed estimation line. Please cancel it first.")
            if rec.is_bom:
                rec.is_bom_remove = True
        parents_to_update = self.mapped('main_product_id')
        res = super(CrmMaterialCost, self).unlink()
        for parent in parents_to_update:
            if parent:
                parent._recompute_parent_margin(parent)

        return res
