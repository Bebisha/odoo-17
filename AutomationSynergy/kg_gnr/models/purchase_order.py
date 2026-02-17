from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    shipment_adv_qty = fields.Float(string="Shipment Advise qty", compute='_compute_shipment_adv_qty')
    shipment_remaing_qty = fields.Float(string="Shipment Remaining qty", compute='_compute_shipment_adv_qty',
                                        readonly=True, force_save=True, store=True)
    so_partner_id = fields.Many2one('res.partner')
    brand_id = fields.Many2one('product.brand',string='Brand')
    country_origin_id = fields.Many2one('res.country', string='Country of Origin')
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', store=True)
    is_complete_git = fields.Boolean(default=False, copy=False, string="Is Complete Git")

    partner_ref = fields.Char(related='order_id.partner_ref')
    sale_cust_id = fields.Many2one('res.partner')

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        vals = super(PurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty,
                                                                       product_uom)
        product = self.product_id.with_context(lang=self.order_id.dest_address_id.lang or self.env.user.lang)
        received_qty = 0
        for rec in picking.shipment_id.shipment_summary_lines:
            if rec.product_id == product:
                received_qty = rec.received_packaging_qty
        vals['quantity'] = received_qty

        return vals

    # @api.onchange('product_id')
    # def product_id_change(self):
    #     vals = {}
    #     if self.product_id:
    #         vals['name'] = self.product_id.name
    #         vals['brand_id'] = self.product_id.brand_id.name
    #         # vals['country_origin_id'] = self.product_id.country_of_origin.id
    #     self.update(vals)

    @api.depends('order_id.date_order')
    def get_date_details(self):
        for rec in self:
            date_issue = rec.order_id.date_order
            date_apr = rec.order_id.date_approve
            if date_issue:
                rec.po_issue_date = date_issue.date()
            else:
                rec.po_issue_date = False
            if date_apr:
                rec.po_date_approve = date_apr.date()
            else:
                rec.po_date_approve = False
            rec.state = rec.order_id.state

    po_name = fields.Char(related='order_id.name')
    po_issue_date = fields.Date(compute=get_date_details)
    po_date_approve = fields.Date()
    state = fields.Char(compute=get_date_details, store=True)
    ignored_remaining = fields.Boolean(defaul=False)

    def ignore_remaining(self):
        for rec in self:
            rec.ignored_remaining = True

    @api.depends('ignored_remaining', 'qty_received', 'product_qty', 'qty_received_manual')
    def _compute_shipment_adv_qty(self):
        for line in self:
            shipment_lines = self.env['shipment.advice.line'].search(
                [('purchase_line_id', '=', line.id), ('state', '!=', 'cancel')])
            shipment_adv_qty = sum(shipment_lines.mapped('shipped_packaging_qty'))
            received_qty = sum(shipment_lines.mapped('received_packaging_qty'))
            if line.ignored_remaining:
                line.shipment_remaing_qty = 0
            else:
                line.shipment_remaing_qty = line.product_uom_qty - received_qty
            line.shipment_adv_qty = shipment_adv_qty


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_git = fields.Boolean("Is GIT?" , default = False, copy=False)
    shipment_id = fields.Many2one('shipment.advice', store=True,copy=False)
    purchase_type = fields.Selection(
        [('local_purchase', 'Local Purchase'), ('meast', 'Middle east'), ('international', 'International'), ('sisconcern', 'Sister Concern'),], string='Purchase Type', default="local_purchase",related='partner_id.purchase_type')
    #
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.purchase_type = self.partner_id.purchase_type
        else:
            self.purchase_type = False

    def _create_picking(self):
        """Should not allow purchase order creating picking as it will be created while confirming the shipment."""
        if not self.company_id.is_default_picking and not self.is_git and self.purchase_type !='local_purchase':
            return False
        else:
            StockPicking = self.env['stock.picking']
            for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
                if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                    order = order.with_company(order.company_id)
                    pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                    if not pickings:
                        res = order._prepare_picking()
                        picking = StockPicking.with_user(SUPERUSER_ID).create(res)

                        pickings = picking
                    else:
                        picking = pickings[0]
                    if self.shipment_id:
                        picking.write({
                            'shipment_id': self.shipment_id.id
                        })
                    moves = order.order_line._create_stock_moves(picking)
                    moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                    seq = 0
                    for move in sorted(moves, key=lambda move: move.date):
                        seq += 5
                        move.sequence = seq
                    moves._action_assign()
                    # Get following pickings (created by push rules) to confirm them as well.
                    forward_pickings = self.env['stock.picking']._get_impacted_pickings(moves)
                    (pickings | forward_pickings).action_confirm()
                    picking.message_post_with_source(
                        'mail.message_origin_link',
                        render_values={'self': picking, 'origin': order},
                        subtype_xmlid='mail.mt_note',
                    )

    # def _create_picking(self):
        # StockPicking = self.env['stock.picking']
        # for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
        #     if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
        #         order = order.with_company(order.company_id)
        #         pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        #         if not pickings:
        #             res = order._prepare_picking()
        #             picking = StockPicking.with_user(SUPERUSER_ID).create(res)
        #
        #             pickings = picking
        #         else:
        #             picking = pickings[0]
        #         if self.shipment_id:
        #             picking.write({
        #                 'shipment_id': self.shipment_id.id
        #             })
        #         moves = order.order_line._create_stock_moves(picking)
        #         moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
        #         seq = 0
        #         for move in sorted(moves, key=lambda move: move.date):
        #             seq += 5
        #             move.sequence = seq
        #         moves._action_assign()
        #         # Get following pickings (created by push rules) to confirm them as well.
        #         forward_pickings = self.env['stock.picking']._get_impacted_pickings(moves)
        #         (pickings | forward_pickings).action_confirm()
        #         picking.message_post_with_source(
        #             'mail.message_origin_link',
        #             render_values={'self': picking, 'origin': order},
        #             subtype_xmlid='mail.mt_note',
        #         )
        # return True
