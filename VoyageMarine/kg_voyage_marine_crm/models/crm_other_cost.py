from odoo import fields, models, api
from odoo.exceptions import ValidationError


class CrmOtherCost(models.Model):
    _name = 'crm.other.cost'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "CRM Other Cost"

    other_cost_id = fields.Many2one('crm.estimation')
    product_id = fields.Many2one('product.product', string="Product")
    description = fields.Char(string='Description')
    quantity = fields.Float(string='Qty', default=1)
    uom_id = fields.Many2one('uom.uom', string='UOM')
    unit_price = fields.Float(string='Unit Price')
    total = fields.Float(string='Total', compute='compute_total')
    margin = fields.Float(string='Margin %', readonly=False)
    subtotal = fields.Float(string='Subtotal', compute='compute_subtotal')
    currency_id = fields.Many2one("res.currency", related="other_cost_id.currency_id", string="Currency")
    company_id = fields.Many2one("res.company", related="other_cost_id.company_id", string="Company")
    inspection_calibration_id = fields.Many2one('inspection.calibration', string="Inspection")

    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False, help="Technical field for UX purpose.")

    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])

    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'),('ft','FT')
    ], string="Code")

    main_product_id = fields.Many2one("crm.other.cost", string="Main Product Reference")
    is_sub_item = fields.Boolean(default=False, string="Subitem")
    sub_item_ids = fields.Many2many("crm.other.cost", string="Subitems", compute="compute_subitems", copy=True,)

    total_subitems = fields.Float(string="Total Subitems", compute="compute_total_subitems")

    is_confirm = fields.Boolean(default=False, string="IS confirm", compute="compute_is_confirm")

    sl_no = fields.Char(string="Sl.No", readonly=False)

    subitems_total = fields.Float(string="Subitems Total", compute="compute_subitems")
    total_unit_price = fields.Float(string="Total Unit Price", compute="compute_total_unit_price")
    is_bom = fields.Boolean(default=False, string="IS confirm",copy=False )
    margin_amount = fields.Float(string='Margin Amount')

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

            subitems = self.env['crm.other.cost'].search([
                ('main_product_id', '=', rec.id)
            ])

            if not subitems:
                continue

            total_sub_qty = sum(subitems.mapped('quantity'))
            total_sub_amount = sum(subitems.mapped('total'))
            if total_sub_qty > 0 and rec.quantity > 0:
                rec.unit_price = total_sub_amount / rec.quantity
            else:
                rec.unit_price = 0.0

    def write(self, vals):
        res = super(CrmOtherCost, self).write(vals)
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
        records = super(CrmOtherCost, self).create(vals_list)
        for rec in records:
            if rec.main_product_id:
                rec._recompute_parent_margin(rec.main_product_id)
        return records

    @api.onchange('subitems_total', 'quantity')
    def _onchange_update_unit_price_from_subitems(self):
        for rec in self:
            print("kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
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

    @api.onchange('other_cost_id.other_cost_ids', 'code')
    def _get_line_numbers(self):
        for line in self:
            line_num = 1
            for line_rec in line.other_cost_id.other_cost_ids:
                if not line_rec.sl_no:
                    if line_rec.code:
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

    @api.onchange('unit_price')
    def check_product_price(self):
        for rec in self:

            if rec.product_id.currency_id != rec.currency_id:
                price_in_product_currency = rec.currency_id._convert(
                    rec.unit_price, rec.product_id.currency_id, rec.company_id, rec.other_cost_id.estimate_date
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
    #                 rec.product_id.standard_price, rec.currency_id, rec.company_id, rec.other_cost_id.estimate_date
    #             )
    #             if rec.unit_price < price_in_sale_product_currency and not rec.is_sub_item:
    #                 raise ValidationError(
    #                     "Selling Price cannot be less than Product Cost.\n\t Product Cost is %.2f %s" % (
    #                         rec.product_id.list_price, rec.product_id.currency_id.name))
    #         else:
    #             price_in_product_currency = rec.unit_price
    #             if price_in_product_currency < rec.product_id.list_price and not rec.is_sub_item:
    #                 raise ValidationError(
    #                     "Selling Price cannot be less than Product Cost.\n\t Product Cost is %.2f %s" % (
    #                         rec.product_id.list_price, rec.product_id.currency_id.name))

    def compute_is_confirm(self):
        for rec in self:
            if rec.main_product_id.other_cost_id.status == 'confirm':
                rec.is_confirm = True
            else:
                rec.is_confirm = False

    @api.depends('total')
    def compute_total_subitems(self):
        for rec in self:
            subitems_id = self.env['crm.other.cost'].search([('main_product_id', '=', rec.id)])
            rec.total_subitems = sum(subitems_id.mapped('total')) + rec.total if subitems_id else rec.total

    def compute_subitems(self):
        for rec in self:
            other_ids = self.search([('main_product_id', '=', rec.id)])
            if other_ids:
                rec.sub_item_ids = [(6, 0, other_ids.ids)]
                rec.subitems_total = sum(other_ids.mapped('subtotal'))
            else:
                rec.sub_item_ids = False
                rec.subitems_total = 0.00

    @api.depends('product_id')
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


    def kg_add_subitems(self):
        self.ensure_one()

        domain = [('main_product_id', '=', self.id)]
        context = dict(
            default_main_product_id=self.id,
            default_is_sub_item=True,
        )

        # Find the BoM for this product
        bom = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)
        ], limit=1,order='id asc')
        print(self.product_id.id, "self.main_product_id.product_id.product_tmpl_id.id")
        print(bom, "bom")

        code_list = ['sm', 'fm', 'lm', 'nm', 'cm', 'rm', 'pm', 'om', 'mm', 'em']
        if bom and self.code in code_list:
            for line in bom.bom_line_ids:
                print(line.product_id, line.product_qty, "sub_item details")
                existing = self.env["crm.other.cost"].search([
                    ('main_product_id', '=', self.id),
                    ('product_id', '=', line.product_id.id),
                    ('is_bom', '=', True)
                ], limit=1)

                if not existing:
                    self.env["crm.other.cost"].create({
                        'product_id': line.product_id.id,
                        'description': line.product_id.name,
                        'quantity': line.product_qty,
                        'main_product_id': self.id,
                        'is_bom': True,
                        'code': line.code
                    })

        # Control creation in the context
        if not self.other_cost_id.is_qtn and self.other_cost_id.so_ids:
            context['create'] = False
        else:
            context['create'] = True

        return {
            'type': 'ir.actions.act_window',
            'name': 'Other Costs',
            'view_mode': 'tree',
            'res_model': 'crm.other.cost',
            'domain': domain,
            'context': context,
            'target': 'new'
        }

    def unlink(self):
        for rec in self:
            if rec.is_confirm:
                raise ValidationError("You can not delete a confirmed estimation lines. You must first cancel it.")
        parents_to_update = self.mapped('main_product_id')
        res = super(CrmOtherCost, self).unlink()
        for parent in parents_to_update:
            if parent:
                parent._recompute_parent_margin(parent)

        return res
