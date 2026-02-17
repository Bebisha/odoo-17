from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class CrmLabourCost(models.Model):
    _name = 'crm.labour.cost'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "CRM Labour Cost"

    labour_cost_id = fields.Many2one('crm.estimation')
    product_id = fields.Many2one('product.product', string="Product")
    description = fields.Text(string='Description')
    quantity = fields.Float(string='Qty', default=1)
    uom_id = fields.Many2one('uom.uom', string='UOM')
    unit_price = fields.Float(string='Unit Price')
    total = fields.Float(string='Total', compute='compute_total')
    margin = fields.Float(string='Margin %', readonly=False)
    margin_amount = fields.Float(string='Margin Amount')
    subtotal = fields.Float(string='Subtotal', compute='compute_subtotal')
    currency_id = fields.Many2one("res.currency", related="labour_cost_id.currency_id", string="Currency")
    company_id = fields.Many2one("res.company", related="labour_cost_id.company_id", string="Company")
    name = fields.Char()
    inspection_calibration_id = fields.Many2one('inspection.calibration', string="Inspection")

    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False, help="Technical field for UX purpose.")

    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', depends=['product_id'])

    code = fields.Selection([
        ('tl', 'TL'),
        ('fl', 'FL'),
        ('sl', 'SL'),
        ('nl', 'NL'),
        ('cl', 'CL'),
        ('rl', 'RL'),
        ('pl', 'PL'),
        ('ml', 'MI'),
        ('el', 'EL'),('ft','FT')
    ], string="Code")
    is_bom = fields.Boolean(string="IS confirm",copy=False )

    main_product_id = fields.Many2one("crm.labour.cost", string="Main Product Reference",copy=True)
    is_sub_item = fields.Boolean(default=False, string="Subitem")
    sub_item_ids = fields.Many2many("crm.labour.cost", string="Subitems", compute="compute_subitems", copy=True)

    total_subitems = fields.Float(string="Total Subitems", compute="compute_total_subitems")

    is_confirm = fields.Boolean(default=False, string="IS confirm", compute="compute_is_confirm")

    sl_no = fields.Char(string="Sl.No", readonly=False)
    des = fields.Text(string='Description', readonly=False, copy=True, store=True,
                      compute="compute_des")

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
            print(rec,"rec")
            if rec.is_sub_item:
                continue

            subitems = self.env['crm.labour.cost'].search([
                ('main_product_id', '=', rec.id)
            ])

            if not subitems:
                continue

            total_sub_qty = sum(subitems.mapped('quantity'))
            total_sub_amount = sum(subitems.mapped('total'))
            print(total_sub_amount,"total_sub_amount")

            if total_sub_qty > 0 and rec.quantity > 0:
                rec.unit_price = total_sub_amount / rec.quantity
            else:
                rec.unit_price = 0.0

    def _check_fl_ft_configuration(self):
        missing_config_products = []

        for line in self:
            if (
                    line.code in ('fl', 'ft') and
                    line.product_id and
                    (
                            line.product_id.detailed_type != 'service' or
                            line.product_id.service_tracking != 'task_in_project'
                    )
            ):
                missing_config_products.append(line.product_id.display_name)

        if missing_config_products:
            product_names_str = ", ".join(set(missing_config_products))
            raise ValidationError(_(
                "Please configure the following products for FL / FT labour:\n\n%s\n\n"
                "Required configuration:\n"
                "- Product Type: Service\n"
                "- Service Tracking: Create a task in an existing project"
            ) % product_names_str)

    def write(self, vals):
        res = super(CrmLabourCost, self).write(vals)
        self._check_fl_ft_configuration()
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
        records = super(CrmLabourCost, self).create(vals_list)
        records._check_fl_ft_configuration()
        for rec in records:
            if rec.main_product_id:
                rec._recompute_parent_margin(rec.main_product_id)
        return records

    @api.onchange('subitems_total', 'quantity')
    def _onchange_update_unit_price_from_subitems(self):
        for rec in self:
            if not rec.is_sub_item:
                rec._update_main_unit_price_from_subitems()

    @api.onchange('quantity', 'unit_price', 'subitems_total')
    def _onchange_quantity_update_total(self):
        for rec in self:
            base_total = (rec.quantity or 0.0) * (rec.unit_price or 0.0)
            rec.total = base_total + (rec.subitems_total or 0.0)

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


    @api.depends('main_product_id')
    def compute_des(self):
        for rec in self:
            if rec.main_product_id:
                rec.des = rec.main_product_id.description
                print(f"Main Product ID: {rec.main_product_id.id}, Description: {rec.main_product_id.description}")
            else:
                rec.des = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.des = rec.main_product_id.description
            else:
                rec.des =''

    subitems_total = fields.Float(string="Subitems Total", compute="compute_subitems")
    total_unit_price = fields.Float(string="Total Unit Price", compute="compute_total_unit_price")

    @api.depends('unit_price', 'quantity')
    def compute_total_unit_price(self):
        for rec in self:
            base_total = rec.quantity * rec.unit_price
            rec.total_unit_price = base_total

    @api.onchange('labour_cost_id.labour_cost_ids', 'code')
    def _get_line_numbers(self):
        for line in self:
            line_num = 1
            for line_rec in line.labour_cost_id.labour_cost_ids:
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

    def compute_is_confirm(self):
        for rec in self:
            if rec.main_product_id.labour_cost_id.status == 'confirm':
                rec.is_confirm = True
            else:
                rec.is_confirm = False

    @api.depends('total')
    def compute_total_subitems(self):
        for rec in self:
            subitems_id = self.env['crm.labour.cost'].search([('main_product_id', '=', rec.id)])
            rec.total_subitems = sum(subitems_id.mapped('total')) + rec.total if subitems_id else rec.total

    def compute_subitems(self):
        for rec in self:
            labour_ids = self.search([('main_product_id', '=', rec.id)])
            if labour_ids:
                rec.sub_item_ids = [(6, 0, labour_ids.ids)]
                rec.subitems_total = sum(labour_ids.mapped('subtotal'))
            else:
                rec.sub_item_ids = False
                rec.subitems_total = 0.00

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

    @api.onchange('product_id')
    def onchange_product(self):
        for product in self:
            product.description = product.product_id.name
            product.uom_id = product.product_id.uom_id.id
            product.unit_price = product.product_id.lst_price

    def kg_add_subitems(self):
        self.ensure_one()

        print(self.main_product_id.description, "self.main_product_id.description")

        domain = [('main_product_id', '=', self.id)]
        context = dict(
            default_main_product_id=self.id,
            default_is_sub_item=True,
            default_des=self.description
        )
        print(context, "context")

        # Fetch BOM for the main product
        bom = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)
        ], limit=1,order='id asc')

        print(self.product_id.id, "self.main_product_id.product_id.product_tmpl_id.id")
        print(self.product_id.product_tmpl_id.id, "self.main_product_id.product_id.product_tmpl_id.id")
        print(bom, "bom")

        # Only allow creation if code matches
        code_list = ['sm', 'fm', 'lm', 'nm', 'cm', 'rm', 'pm', 'om', 'mm', 'em']
        if bom and self.code in code_list:
            for line in bom.bom_line_ids:
                print(line.product_id, line.product_qty, "sub_item details")

                # Check for existing record to avoid duplicates
                existing = self.env["crm.labour.cost"].search([
                    ('main_product_id', '=', self.id),
                    ('product_id', '=', line.product_id.id),
                    ('is_bom', '=', True)
                ], limit=1)

                if not existing:
                    self.env["crm.labour.cost"].create({
                        'product_id': line.product_id.id,
                        'description': line.product_id.name,
                        'quantity': line.product_qty,
                        'main_product_id': self.id,
                        'is_bom': True,
                        'code':line.code
                    })

        # Control creation flag in context
        if not self.labour_cost_id.is_qtn and self.labour_cost_id.so_ids:
            context['create'] = False
        else:
            context['create'] = True

        return {
            'type': 'ir.actions.act_window',
            'name': 'Labour Costs',
            'view_mode': 'tree',
            'res_model': 'crm.labour.cost',
            'domain': domain,
            'context': context,
            'target': 'new'
        }

    @api.onchange('unit_price')
    def check_product_price(self):
        for rec in self:
            if rec.product_id.currency_id != rec.currency_id:
                price_in_product_currency = rec.currency_id._convert(
                    rec.unit_price, rec.product_id.currency_id, rec.company_id,  rec.labour_cost_id.estimate_date
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
    #                 rec.product_id.standard_price, rec.currency_id, rec.company_id, rec.labour_cost_id.estimate_date
    #             )
    #             if  rec.unit_price <  price_in_sale_product_currency and not rec.is_sub_item:
    #                 raise ValidationError(
    #                     "Selling Price cannot be less than Product Cost.\n\t Product Cost is %.2f %s" % (
    #                         rec.product_id.list_price, rec.product_id.currency_id.name))
    #         else:
    #             price_in_product_currency = rec.unit_price
    #             if price_in_product_currency < rec.product_id.list_price and not rec.is_sub_item:
    #                 raise ValidationError(
    #                     "Selling Price cannot be less than Product Cost.\n\t Product Cost is %.2f %s" % (
    #                         rec.product_id.list_price, rec.product_id.currency_id.name))

    def unlink(self):
        for rec in self:
            if rec.is_confirm:
                raise ValidationError("You can not delete a confirmed estimation lines. You must first cancel it.")
        parents_to_update = self.mapped('main_product_id')
        res = super(CrmLabourCost, self).unlink()
        for parent in parents_to_update:
            if parent:
                parent._recompute_parent_margin(parent)

        return res

