from collections import defaultdict
from datetime import time, datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockCustoms(models.Model):
    _inherit = 'stock.picking'
    _description = 'stock customizations'

    shipment_id = fields.Many2one('shipment.advice')

    origin_country_id = fields.Many2one('res.country')
    currency_id = fields.Many2one('res.currency')
    boe_value = fields.Float()

    def _sanity_check(self, separate_pickings=True):
        """ Sanity check for `button_validate()`
            :param separate_pickings: Indicates if pickings should be checked independently for lot/serial numbers or not.
        """
        pickings_without_lots = self.browse()
        products_without_lots = self.env['product.product']
        pickings_without_moves = self.filtered(lambda p: not p.move_ids and not p.move_line_ids)
        precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        no_quantities_done_ids = set()
        pickings_without_quantities = self.env['stock.picking']
        for picking in self:
            if all(float_is_zero(move.quantity, precision_digits=precision_digits) for move in
                   picking.move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))):
                pickings_without_quantities |= picking

        pickings_using_lots = self.filtered(
            lambda p: p.picking_type_id.use_create_lots or p.picking_type_id.use_existing_lots)
        if pickings_using_lots:
            lines_to_check = pickings_using_lots._get_lot_move_lines_for_sanity_check(no_quantities_done_ids,
                                                                                      separate_pickings)
            lines_to_check = self.env['stock.move.line'].browse(self.move_ids.move_line_ids.ids)
            for line in lines_to_check:
                if not line.lot_name and not line.lot_id:
                    pickings_without_lots |= line.picking_id
                    products_without_lots |= line.product_id
        if not self._should_show_transfers():
            if pickings_without_moves:
                raise UserError(
                    _("You can’t validate an empty transfer. Please add some products to move before proceeding."))
            if pickings_without_quantities:
                raise UserError(self._get_without_quantities_error_message())
            if pickings_without_lots:
                for rec in pickings_without_lots.move_line_ids:
                    timestamp_str = str(datetime.today())

                    # Convert the string to a datetime object
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")

                    # Extract milliseconds using strftime
                    milliseconds = timestamp.strftime("%f")[:-3]
                    rec.lot_name = pickings_without_lots.name + '-' + milliseconds
        else:
            message = ""
            if pickings_without_moves:
                message += _('Transfers %s: Please add some items to move.',
                             ', '.join(pickings_without_moves.mapped('name')))
            if pickings_without_lots:
                message += _('\n\nTransfers %s: You need to supply a Lot/Serial number for products %s.',
                             ', '.join(pickings_without_lots.mapped('name')),
                             ', '.join(products_without_lots.mapped('display_name')))
            if message:
                raise UserError(message.lstrip())

    so_boe_type = fields.Selection(
        [('internal', 'Internal Transfer'),
         ('import', 'Import'),
         ], string="OUT BOE Type")

    so_boe_no = fields.Char('OUT BOE No')
    so_ship_no = fields.Char('OUT Ship Doc NO ')
    hs_code = fields.Char('HS CODE')
    coo_code = fields.Char('COO')
    hs_code_out = fields.Char('HS CODE')
    coo_code_out = fields.Char('COO')

    po_boe_type = fields.Selection(
        [('internal', 'Internal Transfer'),
         ('import', 'Import'),
         ], string="IN BOE Type")

    po_boe_no = fields.Char('IN BOE No')
    po_ship_no = fields.Char('IN Ship DOC No')

    def open_boe_stock(self):
        return {
            'name': 'BOE',
            'type': 'ir.actions.act_window',
            'res_model': 'boe.wizard',
            'view_mode': 'form',
            'context': {'default_stock_ids': self.ids, },
            'target': 'new',
        }
        # return {
        #     'name': 'BOE',
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'shipment.advice',
        #     'view_mode': 'form',
        #     'context': {'default_stock_ids': self.ids, },
        #     'target': 'new',
        # }


class StockMoveCustoms(models.Model):
    _inherit = 'stock.quant'
    _description = 'stock quant'

    cost = fields.Float('Cost', compute='compute_date')
    picking_date = fields.Datetime('Picking Date', compute='compute_date')
    price = fields.Float('Unit Cost')

    @api.model
    def _get_inventory_fields_create(self):
        """ Returns a list of fields user can edit when he want to create a quant in `inventory_mode`.
        """
        return ['product_id', 'owner_id', 'price'] + self._get_inventory_fields_write()

    @api.depends("lot_id")
    def compute_date(self):

        for val in self:
            if val.lot_id.picking_id:
                for rec in val.lot_id.picking_id:
                    self.cost = val.lot_id.unit_price
                    self.picking_date = rec.scheduled_date

            else:
                self.picking_date = False
                self.cost = 0


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    cost = fields.Float('Cost', compute='compute_cost')
    customer_id = fields.Many2one('res.partner', 'Customer', compute='getcustandsupp')
    supplier_id = fields.Many2one('res.partner', 'Supplier', compute='getcustandsupp')
    hs_code = fields.Char('HS CODE')
    coo_code = fields.Char('COO')
    hs_code_out = fields.Char('HS CODE')
    coo_code_out = fields.Char('COO')


    @api.depends('lot_id')
    def compute_cost(self):
        for rec in self:
            cost = 0.00
            if rec.lot_id:
                cost = rec.lot_id.unit_price
            rec.cost = cost

    @api.depends('picking_id')
    def getcustandsupp(self):
        for rec in self:
            if rec.move_id:
                rec.hs_code_out = rec.move_id.hs_code_out
                rec.coo_code_out = rec.move_id.coo_code_out
                rec.coo_code = rec.move_id.coo_code
                rec.hs_code = rec.move_id.hs_code
            code = rec.picking_id.picking_type_id.code
            if code == 'incoming':
                rec.supplier_id = rec.picking_id.partner_id
                rec.customer_id = False
            else:
                rec.supplier_id = False
                rec.customer_id = rec.picking_id.partner_id


class StockLot(models.Model):
    _inherit = 'stock.lot'

    unit_price = fields.Float('unit prize', compute='get_purchase_rate', store=True)
    is_import = fields.Boolean('import')
    unit_price_1 = fields.Float()
    picking_id = fields.Many2many('stock.picking', compute='get_purchase_rate', store=True)
    delvery_id = fields.Many2many(
        'stock.picking',
        'rel_sale_picking_rel',  # Custom relation table name
        'rel_sale_id',  # FK to your current model (must match model ID)
        'rel_picking_id',  # FK to stock.picking ID

        store=True
    )

    @api.depends('purchase_order_ids')
    def get_purchase_rate(self):
        for record in self:
            if len(record.purchase_order_ids) == 1:
                pick_lines = self.env['stock.move.line'].search([
                    ('lot_name', 'in', [record._origin.name]),
                    ('product_id', '=', record.product_id.id)
                ])
                if pick_lines:
                    picking = pick_lines[0].picking_id
                    record.picking_id = [fields.Command.link(picking.id)]
                    related_moves = picking.move_ids_without_package.filtered(
                        lambda m: m.product_id.id == record.product_id.id
                    )
                    hs_codes = related_moves.mapped('hs_code')
                    coo_codes = related_moves.mapped('coo_code')
                    pick_lines.write({
                        'hs_code': hs_codes[0] if hs_codes else False,
                        'coo_code': coo_codes[0] if coo_codes else False,
                    })
                    po_line = self.env['purchase.order.line'].search([
                        ('order_id', '=', record.purchase_order_ids.id),
                        ('product_id', '=', record.product_id.id)
                    ], limit=1)

                    record.unit_price = po_line.price_unit if po_line else 0
                else:
                    record.unit_price = 0
            else:
                record.unit_price = 0

            if record.is_import:
                record.unit_price = record.unit_price_1

    # @api.depends('sale_order_ids')
    # def get_sale_order_ids(self):
    #     for record in self:
    #         print("lllllllllllyyyyyyyy")
    #         if len(record.sale_order_ids) == 1:
    #             print("kkkkkkkkkkkk")
    #             pick_lines = self.env['stock.move.line'].search([
    #                 ('lot_name', 'in', [record._origin.name]),
    #                 ('product_id', '=', record.product_id.id)
    #             ])
    #             print(pick_lines,"pickkkkkkkkkkkkkkkkkk")
    #             if pick_lines:
    #                 picking = pick_lines[0].picking_id
    #                 # record.picking_id = [fields.Command.link(picking.id)]
    #                 related_moves = picking.move_ids_without_package.filtered(
    #                     lambda m: m.product_id.id == record.product_id.id
    #                 )
    #                 print(related_moves,"related_moves")
    #                 hs_code_out = related_moves.mapped('hs_code_out')
    #                 # coo_codes = related_moves.mapped('coo_code')
    #                 pick_lines.write({
    #                     'hs_code': hs_code_out[0] if hs_code_out else False,
    #                     # 'coo_code': coo_codes[0] if coo_codes else False,
    #                 })
                    # po_line = self.env['purchase.order.line'].search([
                    #     ('order_id', '=', record.purchase_order_ids.id),
                    #     ('product_id', '=', record.product_id.id)
                    # ], limit=1)

                    # record.unit_price = po_line.price_unit if po_line else 0
            #     else:
            #         record.unit_price = 0
            # else:
            #     record.unit_price = 0

            # if record.is_import:
            #     record.unit_price = record.unit_price_1


class StockMove(models.Model):
    _inherit = "stock.move"

    hs_code = fields.Char('HS CODE')
    coo_code = fields.Char('COO')
    hs_code_out = fields.Char('HS CODE')
    coo_code_out = fields.Char('COO')


