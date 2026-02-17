from odoo import models, fields, _, api
from odoo.exceptions import ValidationError,UserError


class KGStockPickingInherit(models.Model):
    _inherit = "stock.picking"

    boe_ids = fields.Many2many("mrp.bom", string="BOE", copy=False)
    main_product_line_ids = fields.One2many('main.product.line', 'picking_id', string="Main Products Line")
    customer_id = fields.Many2one("res.partner", string="Customer", compute="compute_customer_address")
    po_ids = fields.Many2many("purchase.order", string="Purchase Reference", compute="compute_po_ids",copy=False)
    lpo = fields.Char(string="LPO")
    lpo_date = fields.Date(string="LPO Date")
    vessel_name = fields.Char(string="Vessel/Project Reference")

    so_ids = fields.Many2many("sale.order", string="Job No")
    so_date = fields.Date(string="SO Date", compute="compute_so_date")
    so_user_id = fields.Many2one("res.users", string="SO Representative", compute="compute_so_user_id")

    partner_shipping_id = fields.Many2one("res.partner", string="Delivery Address")
    partner_invoice_id = fields.Many2one("res.partner", string="Invoice Address")
    expected_arrival_date = fields.Datetime(string="Expected Arrival")
    items_landed_warehouse = fields.Boolean(default=False, string="Items Landed in Warehouse")
    landed_date = fields.Date(string="Landed Date")
    vendor_ids = fields.Many2many("res.partner", string="Supplier PO", compute="compute_supplier_ids")
    payment_term_id = fields.Many2one("account.payment.term", string="Payment Terms", compute="compute_payment_terms")
    incoterms_id = fields.Many2one("account.incoterms", string="Incoterms", compute="compute_incoterms")

    service_product_line_ids = fields.One2many('service.product.line', 'picking_id', string="Service Products Line")

    # delivery_status = fields.Selection([
    #     ('pending', 'Not Delivered'),
    #     ('started', 'Started'),
    #     ('partial', 'Partially Delivered'),
    #     ('full', 'Fully Delivered'),
    #     ('picking_packing', 'Picking & Packing'), ('processing_shipping_documents', 'Processing Shipping Documents'),
    #     ('airway_bill_pending', 'Airway Bill Pending'), ('delivery_hold', 'Delivery Hold'),
    #     ('delivered', 'Delivered'), ('ready_for_pickup', 'Ready for Pickup')
    # ], string='Delivery Status', compute='_compute_delivery_status', store=True)


    # Checklist for Receipt
    checklist_packaging = fields.Boolean("Packaging")
    checklist_physical_condition = fields.Boolean("Physical Condition")
    checklist_delivered_qty = fields.Boolean("Delivered Quantity")
    checklist_shipping_docs = fields.Boolean("Shipping Documents")
    checklist_coc_coo = fields.Boolean("COC / COO")
    checklist_invoice = fields.Boolean("Invoice")
    checklist_expiration_date = fields.Boolean("Expiration Date")

    # Checklist for Delivery Order
    checklist_commercial_invoice = fields.Boolean("Commercial Invoice")
    checklist_packing_list = fields.Boolean("Packing List")
    checklist_coc = fields.Boolean("COC")
    checklist_coo = fields.Boolean("COO")
    checklist_delivery_order = fields.Boolean("Delivery Order")
    checklist_invoice_do = fields.Boolean("Invoice (DO)")
    checklist_payment_received = fields.Boolean("Payment Received")

    is_qty_available = fields.Boolean(default=False, string="Is Qty Available", compute="compute_is_qty_available")
    customer_ref = fields.Char(string="Customer Reference")
    job_delivery_note = fields.Char(string="Delivery Note", copy=False, index=True, readonly=False,
                                    default=lambda self: _('New'))

    lot_ids = fields.Many2many("stock.lot", string="Tracking", compute="compute_lot_ids")
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('partial', 'Partially Invoiced'),
        ('no', 'Nothing to Invoice'),
    ], string="Invoice Status", compute="compute_invoice_status")

    payment_status = fields.Selection(
        [('not_paid', 'Not Paid'), ('in_payment', 'In Payment'), ('paid', 'Paid'), ('partial', 'Partially Paid'),
         ('reversed', 'Reversed'), ('invoicing_legacy', 'Invoicing App Legacy')], string="Payment Status",
        compute="_compute_payment_status")

    def _compute_payment_status(self):
        for rec in self:
            if rec.so_ids:
                so_id = self.env['sale.order'].search([('picking_ids', 'in', rec.id)], limit=1)
                if so_id and so_id.payment_status:
                    rec.payment_status = so_id.payment_status
                else:
                    rec.payment_status = False
            else:
                rec.payment_status = False

    def compute_invoice_status(self):
        for rec in self:
            if rec.so_ids:
                statuses = rec.so_ids.mapped('invoice_status')
                if 'upselling' in statuses:
                    rec.invoice_status = 'upselling'
                elif 'invoiced' in statuses:
                    rec.invoice_status = 'invoiced'
                elif 'to invoice' in statuses:
                    rec.invoice_status = 'to invoice'
                elif 'partial' in statuses:
                    rec.invoice_status = 'partial'
                else:
                    rec.invoice_status = 'no'
            else:
                rec.invoice_status = False

    def compute_lot_ids(self):
        for rec in self:
            move_ids = rec.move_ids_without_package.mapped('lot_ids')
            rec.lot_ids = [(6, 0, move_ids.ids)] if move_ids else False

    def compute_is_qty_available(self):
        for rec in self:
            if rec.move_ids_without_package and all(
                    move.product_qty_available >= move.product_uom_qty for move in rec.move_ids_without_package):
                rec.is_qty_available = True
            else:
                rec.is_qty_available = False

    def button_validate(self):
        if not self.is_qty_available and self.picking_type_code != 'incoming':
            print("llllllllllll")
            # raise ValidationError("Stock is currently unavailable !!")
        return super(KGStockPickingInherit, self).button_validate()

    def compute_supplier_ids(self):
        for rec in self:
            if rec.po_ids:
                vendor_ids = rec.po_ids.mapped('partner_id')
                if vendor_ids:
                    rec.vendor_ids |= vendor_ids
                else:
                    rec.vendor_ids = False
            else:
                rec.vendor_ids = False

    def compute_so_date(self):
        for rec in self:
            if rec.so_ids:
                so_id = self.env['sale.order'].search([('picking_ids', 'in', rec.id)], limit=1)
                if so_id and so_id.date_order:
                    rec.so_date = so_id.date_order.date()
                else:
                    rec.so_date = False
            else:
                rec.so_date = False

    def compute_so_user_id(self):
        for rec in self:
            if rec.so_ids:
                so_id = self.env['sale.order'].search([('picking_ids', 'in', rec.id)], limit=1)
                if so_id and so_id.user_id:
                    rec.so_user_id = so_id.user_id.id
                else:
                    rec.so_user_id = False
            else:
                rec.so_user_id = False

    def compute_payment_terms(self):
        for rec in self:
            if rec.so_ids:
                so_id = self.env['sale.order'].search([('picking_ids', 'in', rec.id)], limit=1)
                if so_id and so_id.payment_term_id:
                    rec.payment_term_id = so_id.payment_term_id.id
                else:
                    rec.payment_term_id = False
            else:
                rec.payment_term_id = False

    def compute_incoterms(self):
        for rec in self:
            if rec.so_ids:
                so_id = self.env['sale.order'].search([('picking_ids', 'in', rec.id)], limit=1)
                if so_id and so_id.incoterm:
                    rec.incoterms_id = so_id.incoterm.id
                else:
                    rec.incoterms_id = False
            else:
                rec.incoterms_id = False

    # def _compute_delivery_status(self):
    #     for rec in self:
    #         if rec.sale_ids and rec.so_ids:
    #             if any(rec.state == 'draft' for order in rec.picking_ids):
    #                 rec.delivery_status = 'picking_packing'
    #             elif all(rec.state in ['done', 'sent'] for order in rec.picking_ids):
    #                 rec.delivery_status = 'processing_shipping_documents'
    #             elif any(rec.state == 'draft' for order in rec.picking_ids):
    #                 rec.delivery_status = 'airway_bill_pending'
    #             elif any(order.state in ['done', 'sent'] and any(
    #                     rec.state == 'waiting' for picking in order.picking_ids) for order in rec.so_ids):
    #                 rec.delivery_status = 'delivery_hold'
    #             # elif all(order.state in ['done', 'sent'] and all(
    #             #         rec.state == 'confirmed' for picking in order.picking_ids) for order in  rec.so_ids):
    #             #     rec.delivery_status = 'started'
    #             elif all(order.state in ['done', 'sent'] and all(
    #                     rec.state == 'assigned' for picking in order.picking_ids) for order in  rec.so_ids):
    #                 rec.delivery_status = 'ready_for_pickup'
    #             elif all(order.state in ['done', 'sent'] and all(
    #                     rec.state == 'done' for picking in order.picking_ids) for order in  rec.so_ids):
    #                 rec.delivery_status = 'delivered'
    #             else:
    #                 rec.delivery_status = 'started'
    #         else:
    #             rec.delivery_status = 'pending'

    def compute_po_ids(self):
        for rec in self:
            rec.po_ids = [(6, 0, rec.so_ids.mapped('po_ids').ids)] if rec.so_ids else []

    def compute_customer_address(self):
        for rec in self:
            if rec.origin:
                sale_id = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
                if sale_id and sale_id.partner_id:
                    rec.customer_id = sale_id.partner_id.id
                else:
                    rec.customer_id = False
            else:
                rec.customer_id = False

    def print_dn(self):
        product_ids = self.env['product.product']
        if self.move_ids_without_package:
            product_ids |= self.move_ids_without_package.mapped('product_id')
        if self.service_product_line_ids:
            product_ids |= self.service_product_line_ids.mapped('product_id')

        return {
            'name': 'Select Products',
            'type': 'ir.actions.act_window',
            'res_model': 'dn.select.products',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_dn_product_ids': [(6, 0, product_ids.ids)],
                'default_product_ids': [(6, 0, product_ids.ids)],
            }
        }

    @api.model_create_multi
    def create(self, vals_list):
        scheduled_dates = []
        for vals in vals_list:
            defaults = self.default_get(['name', 'picking_type_id'])
            picking_type = self.env['stock.picking.type'].browse(
                vals.get('picking_type_id', defaults.get('picking_type_id')))
            destination_location = self.env['stock.location'].browse(
                vals.get('location_dest_id', defaults.get('location_dest_id')))

            if not picking_type.sequence_code:
                raise ValidationError("Picking type code is missing. Please enter it to continue.")
            if not destination_location.barcode:
                raise ValidationError(
                    "The %s location code is missing. Please enter it to continue." % destination_location.complete_name)

            if picking_type and picking_type.sequence_id and picking_type.sequence_code and destination_location.barcode:
                if picking_type.sequence_id.prefix:
                    picking_type.sequence_id.prefix = False
                vals['name'] = str(picking_type.sequence_code) + '_' + str(
                    destination_location.barcode) + picking_type.sequence_id.next_by_id()

            scheduled_dates.append(vals.pop('scheduled_date', False))

        pickings = super().create(vals_list)

        for picking, scheduled_date in zip(pickings, scheduled_dates):
            if scheduled_date:
                picking.with_context(mail_notrack=True).write({'scheduled_date': scheduled_date})
        pickings._autoconfirm_picking()

        for picking, vals in zip(pickings, vals_list):
            if vals.get('partner_id'):
                if picking.location_id.usage == 'supplier' or picking.location_dest_id.usage == 'customer':
                    picking.message_subscribe([vals.get('partner_id')])
            if vals.get('picking_type_id'):
                for move in picking.move_ids:
                    if not move.description_picking:
                        move.description_picking = move.product_id.with_context(lang=move._get_lang())._get_description(
                            move.picking_id.picking_type_id)
        return pickings

    def write(self, vals):
        if vals.get('picking_type_id') and any(picking.state != 'draft' for picking in self):
            raise UserError(_("Changing the operation type of this record is forbidden at this point."))
        if vals.get('partner_id'):
            for picking in self:
                if picking.location_id.usage == 'supplier' or picking.location_dest_id.usage == 'customer':
                    if picking.partner_id:
                        picking.message_unsubscribe(picking.partner_id.ids)
                    picking.message_subscribe([vals.get('partner_id')])

        res = super(models.Model, self).write(vals)
        if vals.get('signature'):
            for picking in self:
                picking._attach_sign()
        after_vals = {}
        if vals.get('location_id'):
            after_vals['location_id'] = vals['location_id']
        if vals.get('location_dest_id'):
            after_vals['location_dest_id'] = vals['location_dest_id']
        if 'partner_id' in vals:
            after_vals['partner_id'] = vals['partner_id']
        if after_vals:
            self.move_ids.filtered(lambda move: not move.scrapped).write(after_vals)
        if vals.get('move_ids') or vals.get('move_ids_without_package'):
            self._autoconfirm_picking()
        self._update_picking_custom_sequence(vals)
        return res

    def _update_picking_custom_sequence(self, vals):
        both_change = vals.get('picking_type_id') and vals.get('location_dest_id')
        if both_change:
            picking_type = self.env['stock.picking.type'].browse(vals['picking_type_id'])
            destination_location = self.env['stock.location'].browse(vals['location_dest_id'])
            if not picking_type.sequence_code:
                raise ValidationError("Picking type code missing.")
            if not destination_location.barcode:
                raise ValidationError("The %s barcode is missing." % destination_location.complete_name)
            for picking in self:
                sequence = picking_type.sequence_id
                if sequence.number_next_actual > 1:
                    sequence.write({'number_next_actual': sequence.number_next_actual - 1})
                picking.name = "%s_%s%s" % (picking_type.sequence_code, destination_location.barcode,sequence.next_by_id())
            return

        if vals.get('picking_type_id'):
            picking_type = self.env['stock.picking.type'].browse(vals['picking_type_id'])
            destination_location = self.location_dest_id
            if not picking_type.sequence_code:
                raise ValidationError("Picking type code missing.")
            if not destination_location.barcode:
                raise ValidationError("The %s location barcode is missing." % destination_location.complete_name)
            for picking in self:
                sequence = picking_type.sequence_id
                if sequence.number_next_actual > 1:
                    sequence.write({'number_next_actual': sequence.number_next_actual - 1})
                picking.name = "%s_%s%s" % (picking_type.sequence_code,destination_location.barcode,sequence.next_by_id())

        if vals.get('location_dest_id'):
            destination_location = self.env['stock.location'].browse(vals['location_dest_id'])
            picking_type = self.picking_type_id
            if not picking_type.sequence_code:
                raise ValidationError("Picking type code missing.")
            if not destination_location.barcode:
                raise ValidationError("The %s location barcode is missing." % destination_location.complete_name)
            for picking in self:
                sequence = picking_type.sequence_id
                if sequence.number_next_actual > 1:
                    sequence.write({'number_next_actual': sequence.number_next_actual - 1})
                picking.name = "%s_%s%s" % (picking_type.sequence_code,destination_location.barcode,sequence.next_by_id())
