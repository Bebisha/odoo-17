from odoo.exceptions import ValidationError, UserError

from odoo import models, fields, api, _


class KGCRMEstimation(models.Model):
    _name = "crm.estimation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "CRM Estimation"
    _rec_name = 'display_name'

    @api.depends('name', 'description')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.description:
                rec.display_name = f"{rec.name} - {rec.description}"

    display_name = fields.Char(compute='_compute_display_name')
    name = fields.Char(string="Estimation No")
    description = fields.Char(string="Description")
    scope = fields.Text(string="Scope of Work")

    lead_id = fields.Many2one("crm.lead", string="Lead")
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    estimate_date = fields.Date(string='Estimation Date', default=fields.Date.today())
    bid_closing_date = fields.Date(string='Bid Closing Date', default=fields.Date.today())
    enquiry_no = fields.Char(string='Enquiry No', related='lead_id.enq_no')
    customer_ref = fields.Char(string="Customer Reference")
    attn = fields.Char(string="Attn")
    status = fields.Selection([('new', 'New'),
                               ('confirm', 'Confirmed'),
                               ('cancel', 'Cancelled'),
                               ], default='new', copy=False)
    active = fields.Boolean('Active', default=True, copy=True)
    work_type_id = fields.Many2one('crm.estimation.type', string='Type of work')
    labour_cost_ids = fields.One2many('crm.labour.cost', 'labour_cost_id', string="Labour Cost")
    material_cost_ids = fields.One2many('crm.material.cost', 'material_cost_id', string="Material Cost")
    other_cost_ids = fields.One2many('crm.other.cost', 'other_cost_id', string="Other Cost")
    item_ids = fields.One2many('crm.estimation.item', 'item_id', string="Items")

    labour_cost = fields.Float(string='Total Labour Cost', compute="compute_total")
    material_cost = fields.Float(string='Total Material Cost', compute="compute_total")
    other_cost = fields.Float(string='Total Other Cost', compute="compute_total")
    item_cost = fields.Float(string='Total Items Cost', compute="compute_total")

    total_labour_cost = fields.Float(string='Labour Selling Price', compute="compute_total")
    total_material_cost = fields.Float(string='Material Selling Price', compute="compute_total")
    total_other_cost = fields.Float(string='Other Selling Price', compute="compute_total")
    total_item_cost = fields.Float(string='Items Price', compute="compute_total")

    total_cost = fields.Float(string='Total Cost', compute="compute_total")
    total_estimate = fields.Float(string='Total Estimate', compute="compute_total")
    total_margin = fields.Float(string='Total Margin', compute="compute_total")
    margin_percentage = fields.Float(string="Margin(%)", compute="compute_margin_percentage")
    margin_estimation_cost = fields.Float(default=0.00, string="Margin Estimation Cost", compute="compute_margin")

    tax_id = fields.Many2one('account.tax', string='Taxes', default=lambda self: self.env.company.account_sale_tax_id)

    tax_amount = fields.Float(string="Tax Amount", compute="compute_total")
    total = fields.Float(string="Total with Tax", compute="compute_total")
    po_ids = fields.Many2many("purchase.order", string="Purchase Reference", copy=False)
    est_po_ids = fields.Many2many("purchase.order", 'est_rel', 'est_po_ids_po', compute="compute_po_ids",
                                  string="Purchase Reference")
    so_ids = fields.Many2many("sale.order", string="Sales Reference", copy=False)
    total_estimate_currency = fields.Float(string="Total Estimate (AED)", compute="compute_total_estimate_currency")
    total_material_currency = fields.Float(string="Total Material (AED)", compute="compute_total_material_currency")
    price_list_id = fields.Many2one("product.pricelist", string="Pricelist", domain="[('company_id', '=', company_id)]")
    currency_id = fields.Many2one("res.currency", string="Currency", related='price_list_id.currency_id')
    is_same_scope = fields.Boolean('IS Same Scope', default=False, copy=False)
    vessel_id = fields.Many2one('vessel.code', string='Vessel')
    is_qtn = fields.Boolean(string="Is QTN", default=False, compute="compute_is_qtn")
    enq_po_ids = fields.Many2many("purchase.order", 'est_ids_rel', 'est_id_po_rel', string="Enquiry PO Ref",
                                  compute="compute_enq_po_ids", copy=False, )
    mr_po_ids = fields.Many2many("purchase.order", 'mr_po_ids_rell', 'est_id_po_rel', string="Enquiry PO Ref",
                                 compute="compute_mr_po_ids", copy=False, )

    jr_no = fields.Char('JR.No', copy=False, readonly=True, related="lead_id.jr_no")

    def compute_mr_po_ids(self):
        for rec in self:
            pur_ids = self.env['sale.order'].search([('id', '=', rec.so_ids.ids)])
            if pur_ids and pur_ids.po_ids:
                rec.mr_po_ids = pur_ids.mapped('po_ids')
            else:
                rec.mr_po_ids = False

    #
    def compute_enq_po_ids(self):
        print("jjjjjjjjjjj")
        for rec in self:
            if rec.lead_id and rec.lead_id.po_ids:
                rec.enq_po_ids |= rec.lead_id.po_ids | rec.lead_id.rfq_ids
            else:
                rec.enq_po_ids = False

    est_po_count = fields.Integer(string="Estimated PO Count", compute="compute_po_ids", copy=False, )
    est_rfq_count = fields.Integer(string="Estimated RFQ Count", compute="compute_rfq_ids", copy=False, )

    def compute_po_ids(self):
        print("hhhhhhhhhhhhhhhh")
        for rec in self:
            rec.est_po_ids = rec.enq_po_ids | rec.po_ids | rec.mr_po_ids
            combination_po_ids = rec.enq_po_ids.filtered(lambda po: po.state == 'purchase') | rec.po_ids.filtered(lambda po: po.state == 'purchase') | rec.mr_po_ids.filtered(lambda po: po.state == 'purchase')
            rec.est_po_count = len(combination_po_ids)

    def compute_rfq_ids(self):
        for rec in self:
            rec.est_po_ids = rec.enq_po_ids | rec.po_ids | rec.mr_po_ids
            combination_rfq_ids = rec.enq_po_ids.filtered(lambda po: po.state != 'purchase') | rec.po_ids.filtered(lambda po: po.state != 'purchase') | rec.mr_po_ids.filtered(lambda po: po.state != 'purchase')
            rec.est_rfq_count = len(combination_rfq_ids)

    def update_quotation(self):
        sale_order_vals = []
        rebate_list = []
        sub_sl_no = 0
        rebate = self.env['res.partner'].search([('parent_id', '=', self.partner_id.id),('customer_rank','>', 0)])
        valid_sos = self.so_ids.filtered(lambda so: so.state != 'cancel')

        if valid_sos.filtered(lambda so: so.state == 'draft' and so.qtn_approved):
            raise UserError(
                _("You cannot update this record because a related Sale Order "
                  "is in draft state and has already been approved.")
            )

        for reb in rebate:
            rebate_list.append(reb.id)
        if not self.so_ids or not self.so_ids.filtered(lambda x: x.state == 'draft'):
            sale_order = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
                'order_line': sale_order_vals,
                'state': 'draft',
                'estimation_id': self.id,
                'opportunity_id': self.lead_id.id,
                'order_type': self.lead_id.enquiry_type,
                'estimate_partner_ids': [(6, 0, rebate_list)],
                'pricelist_id': self.price_list_id.id,
                'division_id': self.division_id.id,
                'vessel_id': self.vessel_id.id,
                'customer_reference': self.customer_ref,
                'attn': self.attn,
            })
        else:
            sale_order = self.so_ids.filtered(lambda x: x.state == 'draft')[0]

        def add_subitems(main_obj, sub_model, cost_type,main_line_sl, is_item=False, is_labour=False, is_material=False,
                         is_other=False):
            subitems = self.env[sub_model].search([('main_product_id', '=', main_obj.id)])
            if cost_type == 'is_labour' and main_obj.code == 'fl':
                subitems = subitems.filtered(lambda s: s.code == 'ft')
            for idx, sub in enumerate(subitems, start=1):
                sub_sl_no = f"{main_obj.sl_no}.{idx}"
                is_fl_subitem = False if main_obj.code == 'fl' else sub.code == 'fl'
                sub_vals = {
                    'name': sub.des if cost_type == 'is_labour' else sub.description,
                    'product_id': sub.product_id.id,
                    'product_uom_qty': sub.quantity,
                    'product_uom': sub.uom_id.id,
                    'price_unit': 0.00,
                    'sub_item_price':sub.unit_price,
                    'code': sub.code,
                    'main_line_sl': main_obj.sl_no,
                    'is_fl': is_fl_subitem,
                    'is_subitem': True,
                    'tax_id': False,
                    'order_id': sale_order.id,
                    'sl_no': sub_sl_no,

                }
                # sub_vals._compute_name()
                if is_item:
                    sub_vals['is_items'] = True
                if is_labour:
                    sub_vals['is_labour'] = True
                if is_material:
                    sub_vals['is_material'] = True
                if is_other:
                    sub_vals['is_other'] = True

                # sub_line = self.env['sale.order.line'].create(sub_vals)

                sale_order_vals.append((0, 0, sub_vals))

                # print("===============",sub_line.is_subitem,"sub_line")

        if self.item_ids:
            # for item in sorted(self.item_ids,
            #                    key=lambda i: float(i.sl_no) if isinstance(i.sl_no, (str, bool)) else i.sl_no):
            for item in self.item_ids:
                sub_sl_no += 1
                is_fl_main_item = item.code == 'fl'
                price_unit = item.total_unit_price
                margin = item.margin
                item_vals = {
                    'name': item.description,
                    'product_uom_qty': item.quantity,
                    'product_uom': item.uom_id.id,
                    'price_unit': price_unit,
                    'base_price_unit': price_unit,
                    'margin_per': margin,
                    'code': item.code,
                    'is_items': True,
                    'sl_no': sub_sl_no,
                    'is_fl': is_fl_main_item,
                    'item_id': item.id,
                    'order_id': sale_order.id,
                    'tax_id': [(4, self.tax_id.id)] if self.tax_id else False,
                    # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else False
                }
                # item_line = self.env['sale.order.line'].create(item_vals)
                # print("item_vals", item_vals)
                sale_order_vals.append((0, 0, item_vals))
                add_subitems(item, 'crm.estimation.item','is_items', sub_sl_no, is_item=True)

        if self.labour_cost_ids:
            # for labour in sorted(self.labour_cost_ids, key=lambda l: int(l.sl_no) if str(l.sl_no).isdigit() else 0):
            for labour in self.labour_cost_ids:
                sub_sl_no += 1
                is_fl_main_item = labour.code == 'fl'
                price_unit = labour.total_unit_price
                margin = labour.margin
                labour_vals = {
                    'name': labour.description,
                    'product_id': labour.product_id.id,
                    'product_uom_qty': labour.quantity,
                    'product_uom': labour.uom_id.id,
                    'price_unit': price_unit,
                    'base_price_unit': price_unit,
                    'margin_per': margin,
                    'labour_cost_id': labour.id,
                    'code': labour.code,
                    'sl_no': sub_sl_no,
                    'is_fl': is_fl_main_item,
                    'labour_id': labour.id,
                    'order_id': sale_order.id,
                    'inspection_calibration_id': labour.inspection_calibration_id.id,
                    'tax_id': [(4, self.tax_id.id)] if self.tax_id else False,
                    # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, labour.product_id.taxes_id.ids)]
                }
                sale_order_vals.append((0, 0, labour_vals))
                add_subitems(labour, 'crm.labour.cost','is_labour', sub_sl_no, is_item=True)

        if self.material_cost_ids:
            # for material in sorted(self.material_cost_ids, key=lambda m: m.sl_no):
            for material in self.material_cost_ids:
                sub_sl_no += 1
                is_fl_main_item = material.code == 'fl'
                price_unit = material.total_unit_price
                margin = material.margin
                material_vals = {
                    'name': material.description,
                    'product_id': material.product_id.id,
                    'product_uom_qty': material.quantity,
                    'product_uom': material.uom_id.id,
                    'margin_per': margin,
                    'price_unit': price_unit,
                    'base_price_unit': price_unit,
                    'code': material.code,
                    'sl_no': sub_sl_no,
                    'is_fl': is_fl_main_item,
                    'material_cost_id': material.id,
                    'order_id': sale_order.id,
                    'tax_id': [(4, self.tax_id.id)] if self.tax_id else False,
                    # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, material.product_id.taxes_id.ids)]
                }
                sale_order_vals.append((0, 0, material_vals))
                add_subitems(material, 'crm.material.cost','is_material', sub_sl_no, is_item=True)

        if self.other_cost_ids:
            # for other in sorted(self.other_cost_ids, key=lambda o: o.sl_no):
            for other in self.other_cost_ids:
                sub_sl_no += 1
                is_fl_main_item = other.code == 'fl'
                price_unit = other.total_unit_price
                margin = other.margin
                other_vals = {
                    'name': other.description,
                    'product_id': other.product_id.id,
                    'product_uom_qty': other.quantity,
                    'product_uom': other.uom_id.id,
                    'base_price_unit': price_unit,
                    'price_unit': price_unit,
                    'margin_per': margin,
                    'code': other.code,
                    'sl_no': sub_sl_no,
                    'is_fl': is_fl_main_item,
                    'other_cost_id': other.id,
                    'order_id': sale_order.id,
                    'tax_id': [(4, self.tax_id.id)] if self.tax_id else False,
                    # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, other.product_id.taxes_id.ids)]
                }
                sale_order_vals.append((0, 0, other_vals))
                add_subitems(other, 'crm.other.cost','is_other', sub_sl_no, is_item=True)
        # sorted_order_lines = sale_order_vals
        # order_line_vals = []
        # for line in sorted_order_lines:
        #     print("line", line)
        #     order_line_vals.append((0, 0, {
        #     'name': line[2]['name'],
        #     'product_id': line[2]['product_id.id'],
        #     'product_uom_qty': line[2]['product_uom_qty'],
        #     'product_uom': line[2]['product_uom'],
        #     'price_unit': line[2]['price_unit'],
        #     'main_line_sl': line[2]['main_line_sl'],
        #     'code': line[2].code,
        #     'is_subitem': line[2].is_subitem,
        #     'margin_per': line[2].margin_per,
        #     'sl_no': line[2].sl_no,
        #     'is_fl': line[2].is_fl,
        #     'sub_item_price': line[2].sub_item_price,
        #     'order_id': sale_order.id,
        #     'tax_id': False,
        #     'main_line_id': line[2].main_line_id.id,
        # }))
        print("sale_order_vals", sale_order_vals)
        sale_order.estimation_id = False
        sale_order.order_line = False
        sale_order.write({
            'partner_id': self.partner_id.id,
            'state': 'draft',
            'opportunity_id': self.lead_id.id,
            'order_type': self.lead_id.enquiry_type,
            'estimate_partner_ids': [(6, 0, rebate_list)],
            'pricelist_id': self.price_list_id.id,
            'division_id': self.division_id.id,
            'vessel_id': self.vessel_id.id,
            'order_line': sale_order_vals
        })
        sale_order.estimation_id = self.id
        sale_order._compute_amounts()

    # def update_quotation(self):
    #     sale_order_vals = []
    #     rebate_list = []
    #     sub_sl_no = 0
    #     rebate = self.env['res.partner'].search([('parent_id', '=', self.partner_id.id),('customer_rank','>', 0)])
    #
    #     for reb in rebate:
    #         rebate_list.append(reb.id)
    #     if not self.so_ids or not self.so_ids.filtered(lambda x: x.state == 'draft'):
    #         sale_order = self.env['sale.order'].create({
    #             'partner_id': self.partner_id.id,
    #             'order_line': sale_order_vals,
    #             'state': 'draft',
    #             'estimation_id': self.id,
    #             'opportunity_id': self.lead_id.id,
    #             'order_type': self.lead_id.enquiry_type,
    #             'estimate_partner_ids': [(6, 0, rebate_list)],
    #             'pricelist_id': self.price_list_id.id,
    #             'division_id': self.division_id.id,
    #             'vessel_id': self.vessel_id.id,
    #             'customer_reference': self.customer_ref,
    #             'attn': self.attn,
    #         })
    #     else:
    #         sale_order = self.so_ids.filtered(lambda x: x.state == 'draft')[0]
    #
    #     def add_subitems(main_obj, sub_model, main_line_id, is_item=False, is_labour=False, is_material=False,
    #                      is_other=False):
    #         subitems = self.env[sub_model].search([('main_product_id', '=', main_obj.id)])
    #         for idx, sub in enumerate(subitems, start=1):
    #             sub_sl_no = f"{main_obj.sl_no}.{idx}"
    #             is_fl_subitem = False if main_obj.code == 'fl' else sub.code == 'fl'
    #             sub_vals = {
    #                 'name': getattr(sub, 'description', getattr(sub, 'des', '')),
    #                 'product_id': sub.product_id.id,
    #                 'product_uom_qty': sub.quantity,
    #                 'product_uom': sub.uom_id.id,
    #                 'price_unit': 0.00,
    #                 'sub_item_price':sub.unit_price,
    #                 'code': sub.code,
    #                 'main_line_id': main_line_id.id,
    #                 'is_fl': is_fl_subitem,
    #                 'is_subitem': True,
    #                 'tax_id': False,
    #                 'order_id': sale_order.id,
    #                 'sl_no': sub_sl_no,
    #                 # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, sub.product_id.taxes_id.ids)]
    #             }
    #             print("sub_vals",sub_vals)
    #             if is_item:
    #                 sub_vals['is_items'] = True
    #             if is_labour:
    #                 sub_vals['is_labour'] = True
    #             if is_material:
    #                 sub_vals['is_material'] = True
    #             if is_other:
    #                 sub_vals['is_other'] = True
    #
    #             sub_line = self.env['sale.order.line'].create(sub_vals)
    #             sale_order_vals.append((0, 0, sub_line))
    #
    #             print("===============",sub_line.is_subitem,"sub_line")
    #
    #     if self.item_ids:
    #         # for item in sorted(self.item_ids,
    #         #                    key=lambda i: float(i.sl_no) if isinstance(i.sl_no, (str, bool)) else i.sl_no):
    #         for item in self.item_ids:
    #             sub_sl_no += 1
    #             is_fl_main_item = item.code == 'fl'
    #             price_unit = item.total_unit_price
    #             margin = item.margin
    #             print("margin", margin)
    #             item_vals = {
    #                 'name': item.description,
    #                 'product_uom_qty': item.quantity,
    #                 'product_uom': item.uom_id.id,
    #                 'price_unit': price_unit,
    #                 'margin_per': margin,
    #                 'code': item.code,
    #                 'is_items': True,
    #                 'sl_no': sub_sl_no,
    #                 'is_fl': is_fl_main_item,
    #                 'item_id': item.id,
    #                 'order_id': sale_order.id,
    #                 'tax_id': False,
    #                 # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else False
    #             }
    #             item_line = self.env['sale.order.line'].create(item_vals)
    #             print("item_vals", item_vals)
    #             # sale_order_vals.append((0, 0, item_line))
    #             add_subitems(item, 'crm.estimation.item', item_line, is_item=True)
    #
    #     if self.labour_cost_ids:
    #         # for labour in sorted(self.labour_cost_ids, key=lambda l: int(l.sl_no) if str(l.sl_no).isdigit() else 0):
    #         for labour in self.labour_cost_ids:
    #             sub_sl_no += 1
    #             is_fl_main_item = labour.code == 'fl'
    #             price_unit = labour.total_unit_price
    #             margin = labour.margin
    #             labour_vals = {
    #                 'name': labour.description,
    #                 'product_id': labour.product_id.id,
    #                 'product_uom_qty': labour.quantity,
    #                 'product_uom': labour.uom_id.id,
    #                 'price_unit': price_unit,
    #                 'margin_per': margin,
    #                 'labour_cost_id': labour.id,
    #                 'code': labour.code,
    #                 'sl_no': sub_sl_no,
    #                 'is_fl': is_fl_main_item,
    #                 'labour_id': labour.id,
    #                 'order_id': sale_order.id,
    #                 'inspection_calibration_id': labour.inspection_calibration_id.id,
    #                 'tax_id': False,
    #                 # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, labour.product_id.taxes_id.ids)]
    #             }
    #             labour_line = self.env['sale.order.line'].create(labour_vals)
    #             sale_order_vals.append((0, 0, labour_line))
    #             add_subitems(labour, 'crm.labour.cost', labour_line, is_labour=True)
    #
    #     if self.material_cost_ids:
    #         # for material in sorted(self.material_cost_ids, key=lambda m: m.sl_no):
    #         for material in self.material_cost_ids:
    #             sub_sl_no += 1
    #             is_fl_main_item = material.code == 'fl'
    #             price_unit = material.total_unit_price
    #             margin = material.margin
    #             material_vals = {
    #                 'name': material.description,
    #                 'product_id': material.product_id.id,
    #                 'product_uom_qty': material.quantity,
    #                 'product_uom': material.uom_id.id,
    #                 'margin_per': margin,
    #                 'price_unit': price_unit,
    #                 'code': material.code,
    #                 'sl_no': sub_sl_no,
    #                 'is_fl': is_fl_main_item,
    #                 'material_cost_id': material.id,
    #                 'order_id': sale_order.id,
    #                 'tax_id': False,
    #                 # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, material.product_id.taxes_id.ids)]
    #             }
    #             material_line = self.env['sale.order.line'].create(material_vals)
    #             sale_order_vals.append((0, 0, material_line))
    #             add_subitems(material, 'crm.material.cost', material_line, is_material=True)
    #
    #     if self.other_cost_ids:
    #         # for other in sorted(self.other_cost_ids, key=lambda o: o.sl_no):
    #         for other in self.other_cost_ids:
    #             sub_sl_no += 1
    #             is_fl_main_item = other.code == 'fl'
    #             price_unit = other.total_unit_price
    #             margin = other.margin
    #             other_vals = {
    #                 'name': other.description,
    #                 'product_id': other.product_id.id,
    #                 'product_uom_qty': other.quantity,
    #                 'product_uom': other.uom_id.id,
    #                 'price_unit': price_unit,
    #                 'margin_per': margin,
    #                 'code': other.code,
    #                 'sl_no': sub_sl_no,
    #                 'is_fl': is_fl_main_item,
    #                 'other_cost_id': other.id,
    #                 'order_id': sale_order.id,
    #                 'tax_id': False,
    #                 # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, other.product_id.taxes_id.ids)]
    #             }
    #             other_line = self.env['sale.order.line'].create(other_vals)
    #             sale_order_vals.append((0, 0, other_line))
    #             add_subitems(other, 'crm.other.cost', other_line, is_other=True)
    #     sorted_order_lines = sorted(sale_order_vals, key=lambda x: (
    #         x[2].sl_no is None, x[2].sl_no if x[2].sl_no else 0))
    #     order_line_vals = [(0, 0, {
    #         'name': line[2].name,
    #         'product_id': line[2].product_id.id,
    #         'product_uom_qty': line[2].product_uom_qty,
    #         'product_uom': line[2].product_uom.id,
    #         'price_unit': line[2].price_unit,
    #         'code': line[2].code,
    #         'is_subitem': line[2].is_subitem,
    #         'margin_per': line[2].margin_per,
    #         'sl_no': line[2].sl_no,
    #         'is_fl': line[2].is_fl,
    #         'sub_item_price': line[2].sub_item_price,
    #         'order_id': sale_order.id,
    #         'tax_id': False,
    #         'main_line_id': line[2].main_line_id.id,
    #     }) for line in sorted_order_lines]
    #
    #     sale_order.estimation_id = False
    #     sale_order.order_line = False
    #     sale_order.write({
    #         'partner_id': self.partner_id.id,
    #         'state': 'draft',
    #         'opportunity_id': self.lead_id.id,
    #         'order_type': self.lead_id.enquiry_type,
    #         'estimate_partner_ids': [(6, 0, rebate_list)],
    #         'pricelist_id': self.price_list_id.id,
    #         'division_id': self.division_id.id,
    #         'vessel_id': self.vessel_id.id,
    #         'order_line': order_line_vals
    #     })
    #     sale_order.estimation_id = self.id
    #     sale_order._compute_amounts()

    def compute_is_qtn(self):
        for rec in self:
            if rec.so_ids:
                if any(li.state == 'draft' for li in rec.so_ids):
                    rec.is_qtn = True
                else:
                    rec.is_qtn = False
            else:
                rec.is_qtn = False

    @api.constrains('estimate_date', 'scope')
    def _check_unique_scope_per_day(self):
        for record in self:
            existing_records = self.env['crm.estimation'].search([
                ('id', '!=', record.id),
                ('estimate_date', '=', record.estimate_date),
                ('scope', '=', record.scope),
            ])
            if existing_records:
                self.is_same_scope = True
            else:
                record.is_same_scope = False

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, order=None):
        args = list(args or [])
        if name:
            args += ['|', ('name', operator, name), ('description', operator, name)]
        return self._search(args, limit=limit, order=order)

    @api.onchange('partner_id')
    def get_customer_price_list(self):
        for rec in self:
            if rec.partner_id and rec.partner_id.property_product_pricelist:
                rec.price_list_id = rec.partner_id.property_product_pricelist.id
            else:
                rec.price_list_id = False

    def compute_total_material_currency(self):
        for rec in self:
            if rec.total_material_cost and rec.currency_id and rec.estimate_date:
                if rec.currency_id != self.env.company.currency_id:
                    converted_amount = rec.currency_id._convert(
                        rec.total_material_cost, self.env.company.currency_id, self.env.company,
                        rec.estimate_date
                    )
                    rec.total_material_currency = converted_amount
                else:
                    rec.total_material_currency = rec.total_material_cost
            else:
                rec.total_material_currency = rec.total_material_cost

    def compute_total_estimate_currency(self):
        for rec in self:
            if rec.total_estimate and rec.currency_id and rec.estimate_date:
                if rec.currency_id != self.env.company.currency_id:
                    converted_amount = rec.currency_id._convert(
                        rec.total_estimate, self.env.company.currency_id, self.env.company,
                        rec.estimate_date
                    )
                    rec.total_estimate_currency = converted_amount
                else:
                    rec.total_estimate_currency = rec.total_estimate
            else:
                rec.total_estimate_currency = rec.total_estimate

    @api.model
    def create(self, vals):
        if not vals.get('tax_id'):
            vals['tax_id'] = self.env.company.account_sale_tax_id.id
        return super(KGCRMEstimation, self).create(vals)

    def write(self, vals):
        if 'tax_id' not in vals:
            vals['tax_id'] = self.env.company.account_sale_tax_id.id
        return super(KGCRMEstimation, self).write(vals)

    @api.depends('material_cost_ids', 'labour_cost_ids', 'tax_id')
    def compute_total(self):
        for line in self:
            line.total_material_cost = sum(line.material_cost_ids.mapped('subtotal'))
            line.total_labour_cost = sum(line.labour_cost_ids.mapped('subtotal'))
            line.total_other_cost = sum(line.other_cost_ids.mapped('subtotal'))
            line.total_item_cost = sum(line.item_ids.mapped('subtotal'))

            material_subitems = 0.00
            for vals in line.material_cost_ids:
                sub_material_ids = self.env['crm.material.cost'].search([('main_product_id', '=', vals.id)])
                material_subitems += sum(sub_material_ids.mapped('total'))

            items_subitems = 0.00
            for vals in line.item_ids:
                sub_item_ids = self.env['crm.estimation.item'].search([('main_product_id', '=', vals.id)])
                items_subitems += sum(sub_item_ids.mapped('total'))

            labour_subitems = 0.00
            for vals in line.labour_cost_ids:
                sub_labour_ids = self.env['crm.labour.cost'].search([('main_product_id', '=', vals.id)])
                labour_subitems += sum(sub_labour_ids.mapped('total'))

            other_subitems = 0.00
            for vals in line.other_cost_ids:
                sub_other_ids = self.env['crm.other.cost'].search([('main_product_id', '=', vals.id)])
                other_subitems += sum(sub_other_ids.mapped('total'))

            line.material_cost = sum(line.material_cost_ids.mapped('total'))
            line.labour_cost = sum(line.labour_cost_ids.mapped('total'))
            line.other_cost = sum(line.other_cost_ids.mapped('total'))
            line.item_cost = sum(line.item_ids.mapped('total'))

            total_cost = line.material_cost + line.labour_cost + line.other_cost + line.item_cost
            total_selling_price = line.total_material_cost + line.total_labour_cost + line.total_other_cost + line.total_item_cost

            line.total_estimate = line.total_labour_cost + line.total_material_cost + line.total_other_cost + line.total_item_cost

            line.total_cost = total_cost

            line.total_margin = total_selling_price - total_cost
            tax = (line.tax_id.amount) / 100
            line.tax_amount = tax * line.total_estimate
            line.total = line.total_estimate + line.tax_amount

    def compute_margin_percentage(self):
        for rec in self:
            if rec.total_margin and rec.margin_estimation_cost:
                rec.margin_percentage = (rec.total_margin / rec.margin_estimation_cost) * 100
            else:
                rec.margin_percentage = 0.00

    def compute_margin(self):
        for rec in self:
            labour_ids = rec.labour_cost_ids.filtered(lambda x: x.margin)
            labour_margin = sum(labour_ids.mapped('subtotal'))
            material_ids = rec.material_cost_ids.filtered(lambda x: x.margin)
            material_margin = sum(material_ids.mapped('subtotal'))
            other_ids = rec.other_cost_ids.filtered(lambda x: x.margin)
            other_margin = sum(other_ids.mapped('subtotal'))
            item_ids = rec.item_ids.filtered(lambda x: x.margin)
            item_margin = sum(item_ids.mapped('subtotal'))
            rec.margin_estimation_cost = labour_margin + material_margin + other_margin + item_margin

    def action_confirm(self):
        sale_order_vals = []
        rebate_list = []
        code_list = ['sm', 'fm', 'lm', 'nm', 'cm', 'rm', 'pm', 'om', 'mm', 'em']

        missing_subitems = self.material_cost_ids.filtered(
            lambda sub_item: sub_item.code in code_list and not sub_item.sub_item_ids
        )

        if missing_subitems:
            names = ', '.join(missing_subitems.mapped('product_id.display_name'))
            raise ValidationError(
                "The following main products must have at least one sub-item: %s" % names
            )

        rebate = self.env['res.partner'].search([('parent_id', '=', self.partner_id.id),('customer_rank','>', 0)])
        for reb in rebate:
            rebate_list.append(reb.id)


        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': sorted(sale_order_vals, key=lambda x: (
                x[2].get('sl_no') is None, float(x[2].get('sl_no', 0)) if x[2].get('sl_no') else 0)),
            'state': 'draft',
            'estimation_id': self.id,
            'opportunity_id': self.lead_id.id,
            'order_type': self.lead_id.enquiry_type,
            'estimate_partner_ids': [(6, 0, rebate_list)],
            'pricelist_id': self.price_list_id.id,
            'division_id': self.division_id.id,
            'vessel_id': self.vessel_id.id,
            'customer_reference': self.customer_ref,
            'attn': self.attn,
        })

        def create_subitems(subitems, main_line, cost_type, sl_no_prefix):
            if cost_type == 'is_labour' and main_line.code == 'fl':
                subitems = subitems.filtered(lambda s: s.code == 'ft')
            for idx, subline in enumerate(subitems, start=1):
                is_fl_subitem = subline.code == 'fl' if not main_line.is_fl else False
                subline_sl_no = f"{sl_no_prefix}.{idx}"
                sub_line_vals = {
                    'name': subline.des if cost_type == 'is_labour' else subline.description,
                    'product_id': subline.product_id.id,
                    'product_uom_qty': subline.quantity,
                    'product_uom': subline.uom_id.id,
                    'price_unit': 0.00,
                    'sub_item_price':subline.unit_price,
                    'code': subline.code,
                    'main_line_id': main_line.id,
                    'is_subitem': True,
                    'is_fl': is_fl_subitem,
                    'sl_no': subline_sl_no,
                    'main_line_sl': sl_no_prefix,
                    'order_id': sale_order.id,
                    'manin_product_order_line_id':main_line.id,
                    'tax_id':False,
                    cost_type: True,
                }
                sub_line = self.env['sale.order.line'].create(sub_line_vals)
                sub_line._compute_name()
                sale_order_vals.append((0, 0, sub_line))


        # Items
        if self.item_ids:
            for item in sorted(self.item_ids,
                               key=lambda i: float(i.sl_no) if isinstance(i.sl_no, (str, bool)) else i.sl_no):
                is_fl_main_item = item.code == 'fl'
                item_line_vals = {
                    'name': item.description,
                    'product_uom_qty': item.quantity,
                    'product_uom': item.uom_id.id,
                    'price_unit': (item.subtotal / item.quantity) if item.margin and item.quantity else item.total_unit_price,
                    'base_price_unit': (item.subtotal / item.quantity) if item.margin and item.quantity else item.total_unit_price,
                    'code': item.code,
                    'is_items': True,
                    'sl_no': item.sl_no,
                    'is_fl': is_fl_main_item,
                    'item_id': item.id,
                    'order_id': sale_order.id,
                    'tax_id': [(4, self.tax_id.id)] if self.tax_id else False,
                }
                main_item_line = self.env['sale.order.line'].create(item_line_vals)
                sale_order_vals.append((0, 0, main_item_line))
                subitems = self.env['crm.estimation.item'].search([('main_product_id', '=', item.id)])
                create_subitems(subitems, main_item_line, 'is_items', item.sl_no)

        # Labour Costs
        if self.labour_cost_ids:
            for labour in sorted(self.labour_cost_ids,
                                 key=lambda l: int(l.sl_no) if l.sl_no and str(l.sl_no).isdigit() else 0):
                is_fl_main_item = labour.code == 'fl'
                labour_price_unit = labour.subtotal / labour.quantity if labour.margin else labour.total_unit_price
                labour_line_vals = {
                    'name': labour.description,
                    'product_id': labour.product_id.id,
                    'product_uom_qty': labour.quantity,
                    'product_uom': labour.uom_id.id,
                    'price_unit': labour_price_unit,
                    'base_price_unit': labour_price_unit,
                    'labour_cost_id': labour.id,
                    'code': labour.code,
                    'sl_no': labour.sl_no,
                    'is_fl': is_fl_main_item,
                    'labour_id': labour.id,
                    'order_id': sale_order.id,
                    'inspection_calibration_id': labour.inspection_calibration_id.id,
                    'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, labour.product_id.taxes_id.ids)],
                }
                main_labour_line = self.env['sale.order.line'].create(labour_line_vals)
                sale_order_vals.append((0, 0, main_labour_line))
                subitems = self.env['crm.labour.cost'].search([('main_product_id', '=', labour.id)])
                create_subitems(subitems, main_labour_line, 'is_labour', labour.sl_no)

        # Material Costs
        if self.material_cost_ids:
            for material in sorted(self.material_cost_ids, key=lambda m: m.sl_no):
                is_fl_main_item = material.code == 'fl'
                material_price_unit = material.subtotal / material.quantity if material.margin else material.total_unit_price
                material_line_vals = {
                    'name': material.description,
                    'product_id': material.product_id.id,
                    'product_uom_qty': material.quantity,
                    'product_uom': material.uom_id.id,
                    'price_unit': material_price_unit,
                    'base_price_unit': material_price_unit,
                    'code': material.code,
                    'sl_no': material.sl_no,
                    'is_fl': is_fl_main_item,
                    'material_cost_id': material.id,
                    'order_id': sale_order.id,
                    'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, material.product_id.taxes_id.ids)],
                }
                main_material_line = self.env['sale.order.line'].create(material_line_vals)
                sale_order_vals.append((0, 0, main_material_line))
                subitems = self.env['crm.material.cost'].search([('main_product_id', '=', material.id)])
                create_subitems(subitems, main_material_line, 'is_material', material.sl_no,)

        # Other Costs
        if self.other_cost_ids:
            for other in sorted(self.other_cost_ids, key=lambda o: o.sl_no):
                is_fl_main_item = other.code == 'fl'
                other_price_unit = other.subtotal / other.quantity if other.margin else other.total_unit_price
                other_line_vals = {
                    'name': other.description,
                    'product_id': other.product_id.id,
                    'product_uom_qty': other.quantity,
                    'product_uom': other.uom_id.id,
                    'price_unit': other_price_unit,
                    'base_price_unit': other_price_unit,
                    'code': other.code,
                    'sl_no': other.sl_no,
                    'is_fl': is_fl_main_item,
                    'other_cost_id': other.id,
                    'order_id': sale_order.id,
                    'tax_id': [(4, self.tax_id.id)] if self.tax_id else [(6, 0, other.product_id.taxes_id.ids)],
                }
                main_other_line = self.env['sale.order.line'].create(other_line_vals)
                sale_order_vals.append((0, 0, main_other_line))
                subitems = self.env['crm.other.cost'].search([('main_product_id', '=', other.id)])
                create_subitems(subitems, main_other_line, 'is_other', other.sl_no)

        for line in sale_order.order_line:
            line.order_id = sale_order.id

        self.status = 'confirm'
        self.so_ids |= sale_order

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        default['status'] = 'new'
        new_estimation = super(KGCRMEstimation, self).copy(default=default)
        list_item_ids = []
        list_labour_ids = []
        list_material_ids = []
        list_other_ids = []

        for estimation in self:
            if estimation.item_ids:
                for item in estimation.item_ids:
                    item_vals = {
                        'description': item.description,
                        'quantity': item.quantity,
                        'uom_id': item.uom_id.id if item.uom_id else False,
                        'unit_price': item.unit_price,
                        'margin': item.margin,
                        'code': item.code,
                        'sl_no': item.sl_no,
                    }
                    item_ids = self.env['crm.estimation.item'].create(item_vals)
                    list_item_ids.append(item_ids)

                    for sub_item in item.sub_item_ids:
                        sub_items = {
                            'code': sub_item.code,
                            'product_id': sub_item.product_id.id,
                            'description': sub_item.description,
                            'quantity': sub_item.quantity,
                            'uom_id': sub_item.uom_id.id if sub_item.uom_id else False,
                            'unit_price': sub_item.unit_price,
                            'total': sub_item.total,
                            'is_sub_item': True,
                            'main_product_id': item_ids.id,
                            # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [
                            #     (6, 0, sub_item.product_id.taxes_id.ids)],
                        }
                        self.env['crm.estimation.item'].create(sub_items)

            if estimation.labour_cost_ids:
                for labour in estimation.labour_cost_ids:
                    labour_vals = {
                        'code': labour.code,
                        'product_id': labour.product_id.id,
                        'description': labour.description,
                        'quantity': labour.quantity,
                        'uom_id': labour.uom_id.id if labour.uom_id else False,
                        'unit_price': labour.unit_price,
                        'margin': labour.margin,
                        'margin_amount': labour.margin_amount,
                        'sl_no': labour.sl_no,
                        # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [
                        #     (6, 0, labour.product_id.taxes_id.ids)],
                    }
                    labour_ids = self.env['crm.labour.cost'].create(labour_vals)
                    list_labour_ids.append(labour_ids)

                    for sub_lab in labour.sub_item_ids:
                        sub_labours = {
                            'code': sub_lab.code,
                            'product_id': sub_lab.product_id.id,
                            'description': sub_lab.des,
                            'quantity': sub_lab.quantity,
                            'uom_id': sub_lab.uom_id.id if sub_lab.uom_id else False,
                            'unit_price': sub_lab.unit_price,
                            'total': sub_lab.total,
                            'margin': labour.margin,
                            'is_sub_item': True,
                            'main_product_id': labour_ids.id,
                            # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [
                            #     (6, 0, sub_lab.product_id.taxes_id.ids)],
                        }
                        self.env['crm.labour.cost'].create(sub_labours)

            if estimation.material_cost_ids:
                for material in estimation.material_cost_ids:
                    material_vals = {
                        'code': material.code,
                        'product_id': material.product_id.id,
                        'description': material.description,
                        'quantity': material.quantity,
                        'uom_id': material.uom_id.id if material.uom_id else False,
                        'unit_price': material.unit_price,
                        'margin': material.margin,
                        'margin_amount': material.margin_amount,
                        'sl_no': material.sl_no,
                        # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [
                        #     (6, 0, material.product_id.taxes_id.ids)],
                    }
                    material_ids = self.env['crm.material.cost'].create(material_vals)
                    list_material_ids.append(material_ids)

                    for sub_mat in material.sub_item_ids:
                        sub_materials = {
                            'code': sub_mat.code,
                            'product_id': sub_mat.product_id.id,
                            'description': sub_mat.description,
                            'quantity': sub_mat.quantity,
                            'uom_id': sub_mat.uom_id.id if sub_mat.uom_id else False,
                            'unit_price': sub_mat.unit_price,
                            'total': sub_mat.total,
                            'margin': sub_mat.margin,
                            'is_sub_item': True,
                            'main_product_id': material_ids.id,
                            # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [
                            #     (6, 0, sub_mat.product_id.taxes_id.ids)],
                        }
                        # self.env['crm.material.cost'].create(sub_materials)
                        code_list = ['sm', 'fm', 'lm', 'nm', 'cm', 'rm', 'pm', 'om', 'mm', 'em']
                        if material.code in code_list:
                            self.env['crm.material.cost'].create({})
                        else:
                            self.env['crm.material.cost'].create(sub_materials)

            if estimation.other_cost_ids:
                for other in estimation.other_cost_ids:
                    other_vals = {
                        'code': other.code,
                        'product_id': other.product_id.id,
                        'description': other.description,
                        'quantity': other.quantity,
                        'uom_id': other.uom_id.id if other.uom_id else False,
                        'unit_price': other.unit_price,
                        'margin': other.margin,
                        'margin_amount': other.margin_amount,
                        'sl_no': other.sl_no,
                        # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [
                        #     (6, 0, other.product_id.taxes_id.ids)],
                    }
                    other_ids = self.env['crm.other.cost'].create(other_vals)
                    list_other_ids.append(other_ids)

                    for sub_oth in other.sub_item_ids:
                        sub_others = {
                            'code': sub_oth.code,
                            'product_id': sub_oth.product_id.id,
                            'description': sub_oth.description,
                            'quantity': sub_oth.quantity,
                            'uom_id': sub_oth.uom_id.id if sub_oth.uom_id else False,
                            'unit_price': sub_oth.unit_price,
                            'total': sub_oth.total,
                            'margin': sub_oth.margin,
                            'is_sub_item': True,
                            'main_product_id': other_ids.id,
                            # 'tax_id': [(4, self.tax_id.id)] if self.tax_id else [
                            #     (6, 0, sub_oth.product_id.taxes_id.ids)],
                        }
                        self.env['crm.other.cost'].create(sub_others)

        new_estimation.item_ids = [(6, 0, [item.id for item in list_item_ids])]
        new_estimation.labour_cost_ids = [(6, 0, [labour.id for labour in list_labour_ids])]
        new_estimation.material_cost_ids = [(6, 0, [material.id for material in list_material_ids])]
        new_estimation.other_cost_ids = [(6, 0, [other.id for other in list_other_ids])]

        return new_estimation

    def action_cancel(self):
        self.status = 'cancel'
        if self.so_ids:
            if any(li.qtn_approved for li in self.so_ids):
                raise ValidationError("You cannot cancel an approved quotation estimation")
            for vals in self.so_ids:
                if not vals.qtn_approved:
                    vals.state = 'cancel'

    def reset_to_draft(self):
        self.status = 'new'

    def kg_action_create_rfq(self):
        active_id = self.env['crm.estimation'].browse(self._context.get('active_ids'))

        if not active_id or len(active_id) != 1:
            raise ValidationError(_("Please select exactly one estimation."))

        active_id = active_id[0]
        orderline = []
        has_any = False
        for line in active_id.material_cost_ids:
            order_qty = line.balance_qty or line.quantity
            if (
                    order_qty > 0
                    and line.quantity != line.po_qty
                    and line.product_id
                    and line.product_id.detailed_type != 'service'
            ):
                has_any = True
                orderline.append((0, 0, {
                    'code': line.code,
                    'product_id': line.product_id.id,
                    'qty': order_qty,
                    'units': line.uom_id.id,
                    'price_unit': line.unit_price,
                    'material_cost_id': line.id,
                }))
        for line in active_id.item_ids:
            order_qty = line.balance_qty or line.quantity
            if order_qty > 0 and line.quantity != line.po_qty:
                has_any = True
                orderline.append((0, 0, {
                    'code': line.code,
                    'name': line.description,
                    'qty': order_qty,
                    'units': line.uom_id.id,
                    'price_unit': line.unit_price,
                    'item_id': line.id,
                }))
        print(orderline,"orderline")

        if not has_any:
            raise ValidationError(_("No Material Cost or Item lines available to create RFQ."))

        return {
            'name': 'Create RFQ',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'kg.create.rfq.wizard',
            'target': 'new',
            'context': {
                'default_estimation_id': active_id.id,
                'default_order_line_ids': orderline,
            }
        }

    # def kg_action_create_rfq(self):
    #     # self.ensure_one()
    #     active_id = self
    #
    #     orderline = []
    #     has_material = False
    #     has_item = False
    #
    #     for line in active_id.material_cost_ids:
    #         print(line,"ggggggggggggggggg")
    #         order_qty = max(line.balance_qty, 0) if line.balance_qty else max(line.quantity, 0)
    #
    #         if (
    #                 order_qty > 0
    #                 and line.quantity != line.po_qty
    #                 and line.product_id
    #                 and line.product_id.detailed_type != 'service'
    #         ):
    #             has_material = True
    #             met = {
    #                 'product_id': line.product_id.id,
    #                 'qty': order_qty,
    #                 'units': line.uom_id.id,
    #                 'price_unit': line.unit_price,
    #                 'material_cost_id': line.id,
    #             }
    #             print(met,"met")
    #             orderline.append((0, 0, met ))
    #
    #     for line in active_id.item_ids:
    #         print(line, "22222222222222222222222")
    #         order_qty = max(line.balance_qty, 0) if line.balance_qty else max(line.quantity, 0)
    #
    #         if order_qty > 0 and line.quantity != line.po_qty:
    #             has_item = True
    #             itm = {
    #                 'name': line.description,
    #                 'qty': order_qty,
    #                 'units': line.uom_id.id,
    #                 'price_unit': line.unit_price,
    #                 'item_id': line.id,
    #             }
    #             print(itm,"itm")
    #             orderline.append((0, 0, itm))
    #     print(orderline,"orderline")
    #
    #     if not has_material and not has_item:
    #         raise ValidationError(
    #             _("No Material Cost or Item lines available to create RFQ.")
    #         )
    #
    #     return {
    #         'name': 'Create RFQ',
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'kg.create.rfq.wizard',
    #         'target': 'new',
    #         'context': {
    #             'default_estimation_id': active_id.id,
    #             'default_order_line_ids': orderline,
    #         }
    #     }

    def get_purchase_order(self):
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.est_po_ids.ids),('state', '=', 'purchase')],
            'target': 'current',
            'context': {'create': False}
        }

    def get_rfq_order(self):
        return {
            'name': 'RFQ',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.est_po_ids.ids),('state', '!=', 'purchase')],
            'target': 'current',
            'context': {'create': False}
        }

    def get_sale_order(self):
        return {
            'name': 'Sales Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', 'in', self.so_ids.ids)],
            'target': 'current',
            'context': {'create': False}
        }
