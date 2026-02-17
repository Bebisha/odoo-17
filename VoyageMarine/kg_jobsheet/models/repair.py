from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError
from odoo.tools import format_date, float_compare, float_is_zero


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    vessel = fields.Char(string="Vessel")
    vessel_id = fields.Many2one('vessel.code', string='Vessel')
    job_ref_calibration = fields.Many2one('calibration.form', string="Job reference")
    job_ref_lsa = fields.Many2one('lsa.form', string="Job reference")
    job_ref_ffa = fields.Many2one('ffa.form', string="Job reference")
    job_ref_field_service = fields.Many2one('field.service', string="Job reference")
    job_ref_nav_comm = fields.Many2one('navigation.communication', string="Job reference")
    product_category_id = fields.Many2one('product.category', string="Scope")
    certificate_content_view = fields.Html(string="Certificate Content")
    product_loct_id = fields.Many2one('stock.location', string="Product Location")
    saleorder_id = fields.Many2one("sale.order", string="Sale Order")
    customer_location_id = fields.Many2one('stock.location', string="Customer Location",
                                           )
    lot_vir_id = fields.Many2one('stock.lot', string='Assigned Serials', readonly=False)
    is_calibration_repair = fields.Boolean(string="IS calibration Repair")
    jobsheet_form_count = fields.Integer(
        string="Calibration JobSheet Count",
        compute="_compute_form_counts_jobsheet"
    )
    jobsheet_form_count_ffa = fields.Integer(
        string="Calibration JobSheet Count",
        compute="_compute_form_counts_jobsheet_ffa"
    )
    jobsheet_form_count_lsa = fields.Integer(
        string="Calibration JobSheet Count",
        compute="_compute_form_counts_jobsheet_lsa"
    )
    jobsheet_form_count_field_service = fields.Integer(
        string="Field service JobSheet Count",
        compute="_compute_form_counts_jobsheet_lsa"
    )
    jobsheet_form_count_nav_comm = fields.Integer(
        string="Navigation and comm JobSheet Count",
        compute="_compute_form_counts_jobsheet_lsa"
    )
    sale_form_count = fields.Integer(
        string="SaleOrder Count",
        compute="_compute_form_counts_sale"
    )

    mr_created = fields.Boolean(default=False, copy=False)
    mr_received = fields.Boolean(default=False, copy=False)
    is_line = fields.Boolean(default=False, copy=False, compute="compute_is_lines")
    is_revision_request = fields.Boolean(default=False, copy=False)
    is_revision_approve = fields.Boolean(default=False, copy=False)
    revision_created = fields.Boolean(default=False, copy=False)

    state = fields.Selection(selection_add=[('calibrated', 'Calibrated')],
                             ondelete={'calibrated': 'set default'})
    make = fields.Char(string="Make")
    model = fields.Char(string='Model')
    make_id = fields.Many2one('rec.make', string='Make')
    model_id = fields.Many2one('rec.model', string='Model')
    physical_status_id = fields.Many2one('physical.status', string="Physical Status")
    accesories = fields.Text(string="Accessories")
    remark = fields.Text(string='Remark', copy=False)

    jr_no = fields.Char('JR.No', copy=False, readonly=True, related="saleorder_id.jr_no")


    def compute_is_lines(self):
        for rec in self:
            if rec.move_ids and any(li.repair_line_type == 'add' for li in rec.move_ids) and not rec.revision_created:
                rec.is_line = True
            else:
                rec.is_line = False

    def request_revision(self):
        quantity_problems = []
        price_problems = []
        if self.product_id.lst_price <= 0:
            raise ValidationError(_("Please enter the sales price for the Maninproduct: %s." % self.product_id.name))

        for move in self.move_ids:
            if move.quantity <= 0:
                quantity_problems.append(move.product_id.name)

            if move.product_id.lst_price <= 0:
                price_problems.append(move.product_id.name)

        if quantity_problems:
            raise ValidationError(_(
                "Please enter the demand quantity for the following product(s): %s" % ', '.join(quantity_problems)
            ))

        if price_problems:
            raise ValidationError(_(
                "Please enter the sales price for the following product(s): %s" % ', '.join(price_problems)
            ))

        self.is_revision_request = True

    def approve_revision(self):
        self.is_revision_approve = True

    def revision_reason(self):

        return {
            'name': 'Revision Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'revision.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_id': self.saleorder_id.id,
            }
        }

    def action_sale_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('id', '=', self.saleorder_id.id)],
            'context': {'create': False}
        }

    def _compute_form_counts_sale(self):
        for order in self:
            order.sale_form_count = self.env['sale.order'].search_count([('id', '=', self.saleorder_id.id)])

    def _compute_form_counts_jobsheet(self):
        for order in self:
            order.jobsheet_form_count = self.env['calibration.form'].search_count(
                [('id', '=', self.job_ref_calibration.id)])

    def _compute_form_counts_jobsheet_lsa(self):
        for order in self:
            order.jobsheet_form_count_lsa = self.env['lsa.form'].search_count(
                [('id', '=', self.job_ref_lsa.id)])

    def _compute_form_counts_jobsheet_ffa(self):
        for order in self:
            order.jobsheet_form_count_ffa = self.env['ffa.form'].search_count(
                [('id', '=', self.job_ref_ffa.id)])
            order.jobsheet_form_count_field_service = self.env['field.service'].search_count(
                [('id', '=', self.job_ref_field_service.id)])
            order.jobsheet_form_count_nav_comm = self.env['navigation.communication'].search_count(
                [('id', '=', self.job_ref_nav_comm.id)])

    def action_validate(self):
        self.ensure_one()
        if self.filtered(lambda repair: any(m.product_uom_qty < 0 for m in repair.move_ids)):
            raise UserError(_("You can not enter negative quantities."))
        if not self.product_id or self.product_id.type == 'consu':
            return self._action_repair_confirm()
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        available_qty_owner = sum(self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.location_id.id),
            ('lot_id', '=', self.lot_id.id),
            ('owner_id', '=', self.partner_id.id),
        ]).mapped('quantity'))
        available_qty_noown = sum(self.env['stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.location_id.id),
            ('lot_id', '=', self.lot_id.id),
            ('owner_id', '=', False),
        ]).mapped('quantity'))
        repair_qty = self.product_uom._compute_quantity(self.product_qty, self.product_id.uom_id)
        for available_qty in [available_qty_owner, available_qty_noown]:
            print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv11111111111")
            if float_compare(available_qty, repair_qty, precision_digits=precision) >= 0:
                return self._action_repair_confirm()
        print("iiiiiiiiiiiiiiiiiiii")
        return {
            'name': self.product_id.display_name + _(': Insufficient Quantity To Repair'),
            'view_mode': 'form',
            'res_model': 'stock.warn.insufficient.qty.repair',
            'view_id': self.env.ref('repair.stock_warn_insufficient_qty_repair_form_view').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_product_id': self.product_id.id,
                'default_location_id': self.location_id.id,
                'default_repair_id': self.id,
                'default_lot_id': self.lot_id.id,
                'default_quantity': repair_qty,
                'default_product_uom_name': self.product_id.uom_name
            },
            'target': 'new'
        }


    def action_create_sale_order(self):
        result = super(RepairOrder, self).action_create_sale_order()
        sale_orders = self.env['sale.order'].search([
            ('repair_order_ids', 'in', self.ids)
        ])
        product = self.product_id
        product_qty = self.product_qty
        if sale_orders:
            for order in sale_orders:
                new_line_values = {
                    'order_id': order.id,
                    'product_id': product.id,
                    'product_uom_qty': product_qty,
                    'price_unit': product.list_price,
                    'name': product.name
                }
                # Create the new order line
                self.env['sale.order.line'].create(new_line_values)
        return result

    def action_repair_start(self):
        if not all(li.forecast_availability > 0 and li.repair_line_type == 'add' for li in self.move_ids):
            add_lines = self.move_ids.filtered(lambda m: m.repair_line_type == 'add')
            if len(add_lines) != 0 and not self.mr_received:
                raise ValidationError('Receive the material before staring the repair ')
        quantity_problems = []
        price_problems = []

        for move in self.move_ids:
            if not move.quantity:
                move.quantity = move.product_uom_qty
            if move.quantity <= 0:
                quantity_problems.append(move.product_id.name)

            if move.product_id.lst_price <= 0:
                price_problems.append(move.product_id.name)

        if quantity_problems:
            raise ValidationError(_(
                "Please enter the demand quantity for the following product(s): %s" % ', '.join(quantity_problems)
            ))

        if price_problems:
            raise ValidationError(_(
                "Please enter the sales price for the following product(s): %s" % ', '.join(price_problems)
            ))

        # for vals in self.move_ids:
        #
        #     if vals.quantity <= 0:
        #         raise ValidationError(_("Please enter the demand quantity of the product."))
        #
        #     if vals.product_id.lst_price <= 0:
        #         raise ValidationError(_("Please enter the sales price of the product."))
        result = super(RepairOrder, self).action_repair_start()
        return result

    def action_delivery_repair(self):

        # 1️⃣ All repairs must have a Sale Order
        repairs_without_sale = self.filtered(lambda r: not r.saleorder_id)
        if repairs_without_sale:
            raise ValidationError(_(
                "Delivery cannot be created.\n\n"
                "The following repair(s) are not linked to any Sale Order:\n%s"
            ) % ", ".join(repairs_without_sale.mapped('name')))

        # 2️⃣ All repairs must belong to SAME Sale Order
        sale_orders = self.mapped('saleorder_id')
        if len(sale_orders) > 1:
            raise ValidationError(_(
                "Batch delivery is allowed only for the SAME Sale Order.\n\n"
                "Selected Sale Orders:\n%s"
            ) % ", ".join(sale_orders.mapped('name')))

        if any(repair.state != "under_repair" for repair in self):
            raise ValidationError(_("Delivery can be created only for Under repair records."))
        picking_type = self.env.ref('stock.picking_type_out', raise_if_not_found=False)
        used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations', raise_if_not_found=False)
        repair = self[0]
        dest_location = repair.partner_id.property_stock_customer
        if not picking_type or not used_location:
            raise UserError('Required picking type or location is missing.')
        dev_seq = self.env['ir.sequence'].next_by_code('dn.seq') or '/'
        name = f"DN_{dest_location.name}{dev_seq}"
        picking = self.env['stock.picking'].create({
                # 'name': name,
                'partner_id': repair.partner_id.id,
                'picking_type_id': picking_type.id,
                'location_id': used_location.id,
                'location_dest_id': dest_location.id,
                'move_type': 'direct',
                'origin': repair.name,
                'repair_id': repair.id,
                'lead_id': repair.saleorder_id.opportunity_id.id if repair.saleorder_id.opportunity_id else repair.saleorder_id.estimation_id.lead_id
            })
        for repair in self:
            repair.action_repair_end_batch(picking)

    def action_repair_end_batch(self, picking):
        """ Checks before action_repair_done.
        @return: True
        """
        # Step 1: Handle the case where `move_ids` is missing or has no `repair_line_type`
        if not self.move_ids or not self.move_ids.repair_line_type:
            sale_order = self.saleorder_id
            existing_line = sale_order.order_line.filtered(lambda l: l.product_id == self.product_id)

            if existing_line:
                sale_qty = existing_line.product_uom_qty
                repair_qty = self.product_qty
                existing_line.qty_delivered += repair_qty
                existing_line.balance_qty = sale_qty - repair_qty
            self.state = 'calibrated'
            return True
        if self.filtered(lambda repair: repair.state != 'under_repair'):
            raise UserError(_("Repair must be under repair in order to end reparation."))
        if not self.move_ids:
            raise ValidationError("No moves associated with the repair. Please check the repair process.")

        if any(not li.quantity for li in self.move_ids):
            raise ValidationError("Quantity is required. Please update the quantity before completing the repair.")
        if self.is_calibration_repair and self.saleorder_id:
            sale_order = self.saleorder_id
            existing_line = sale_order.order_line.filtered(lambda l: l.product_id == self.product_id)
            if existing_line:
                sale_qty = existing_line.product_uom_qty
                repair_qty = self.product_qty
                existing_line.qty_delivered += repair_qty
                existing_line.balance_qty = sale_qty - repair_qty

            # Post the message after updating sale order
            message = "Repair completed: Updated delivery quantities for products."
            sale_order.message_post(body=message)
            self.message_post(body=message)

        # Step 4: Check for incomplete or picked moves
        partial_moves = set()
        picked_moves = set()
        for move in self.move_ids:
            if float_compare(move.quantity, move.product_uom_qty, precision_rounding=move.product_uom.rounding) < 0:
                partial_moves.add(move.id)
            if move.picked:
                picked_moves.add(move.id)

        # If there are partial moves or picked moves, return a warning action
        if partial_moves or (picked_moves and len(picked_moves) < len(self.move_ids)):
            ctx = dict(self.env.context or {})
            ctx['default_repair_ids'] = self.ids
            return {
                'name': _('Uncomplete Move(s)'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'views': [(False, 'form')],
                'res_model': 'repair.warn.uncomplete.move',
                'target': 'new',
                'context': ctx,
            }

        return self.action_repair_done_batch(picking)


    def action_repair_done_batch(self,picking):
        """ Creates stock move for final product of repair order.
        Writes move_id and move_ids state to 'done'.
        Writes repair order state to 'Repaired'.
        @return: True
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        product_move_vals = []

        # Cancel moves with 0 quantity
        # self.move_ids.filtered(
        #     lambda m: float_is_zero(m.quantity, precision_rounding=m.product_uom.rounding))._action_cancel()

        self.move_ids._action_cancel()

        no_service_policy = 'service_policy' not in self.env['product.template']
        # SOL qty delivered = repair.move_ids.quantity
        for repair in self:
            if all(not move.picked for move in repair.move_ids):
                repair.move_ids.picked = True
            if repair.sale_order_line_id:
                ro_origin_product = repair.sale_order_line_id.product_template_id
                # TODO: As 'service_policy' only appears with 'sale_project' module, isolate conditions related to this field in a 'sale_project_repair' module if it's worth
                if ro_origin_product.detailed_type == 'service' and (
                        no_service_policy or ro_origin_product.service_policy == 'ordered_prepaid'):
                    repair.sale_order_line_id.qty_delivered = repair.sale_order_line_id.product_uom_qty
            if not repair.product_id:
                continue

            if repair.product_id.product_tmpl_id.tracking != 'none' and not repair.lot_id:
                raise ValidationError(_(
                    "Serial number is required for product to repair : %s",
                    repair.product_id.display_name
                ))

            # Try to create move with the appropriate owner
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id,
                                                                                  repair.product_loct_id,
                                                                                  repair.lot_id,
                                                                                  owner_id=repair.partner_id,
                                                                                  strict=True)
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id
            product_move_vals.append({
                'name': repair.name,
                'product_id': repair.product_id.id,
                'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                'product_uom_qty': repair.product_qty,
                'partner_id': repair.partner_id.id,
                'location_id': repair.location_id.id,
                'location_dest_id': repair.customer_location_id.id,
                'picked': True,
                'picking_id': picking.id,
                # 'picking_id': False,
                'move_line_ids': [(0, 0, {
                    'product_id': repair.product_id.id,
                    'lot_id': repair.lot_id.id,
                    'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
                    'quantity': repair.product_qty,
                    'package_id': False,
                    'result_package_id': False,
                    'owner_id': owner_id,
                    'location_id': repair.product_loct_id.id,
                    'company_id': repair.company_id.id,
                    'location_dest_id': repair.customer_location_id.id,
                    'consume_line_ids': [(6, 0, repair.move_ids.move_line_ids.ids)]
                })],
                'repair_id': repair.id,
                'origin': repair.name,
                'company_id': repair.company_id.id,
            })

        product_moves = self.env['stock.move'].create(product_move_vals)
        repair_move = {m.repair_id.id: m for m in product_moves}
        for repair in self:
            move_id = repair_move.get(repair.id, False)
            if move_id:
                repair.move_id = move_id
        all_moves = self.move_ids + product_moves
        all_moves._action_done(cancel_backorder=True)

        for sale_line in self.move_ids.sale_line_id:
            price_unit = sale_line.price_unit
            sale_line.write({'product_uom_qty': sale_line.qty_delivered, 'price_unit': price_unit})
        self.state = 'done'

    def action_repair_done(self):
        """ Creates stock move for final product of repair order.
        Writes move_id and move_ids state to 'done'.
        Writes repair order state to 'Repaired'.
        @return: True
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        product_move_vals = []

        # Cancel moves with 0 quantity
        # self.move_ids.filtered(
        #     lambda m: float_is_zero(m.quantity, precision_rounding=m.product_uom.rounding))._action_cancel()

        self.move_ids._action_cancel()

        no_service_policy = 'service_policy' not in self.env['product.template']
        # SOL qty delivered = repair.move_ids.quantity
        for repair in self:
            if all(not move.picked for move in repair.move_ids):
                repair.move_ids.picked = True
            if repair.sale_order_line_id:
                ro_origin_product = repair.sale_order_line_id.product_template_id
                # TODO: As 'service_policy' only appears with 'sale_project' module, isolate conditions related to this field in a 'sale_project_repair' module if it's worth
                if ro_origin_product.detailed_type == 'service' and (
                        no_service_policy or ro_origin_product.service_policy == 'ordered_prepaid'):
                    repair.sale_order_line_id.qty_delivered = repair.sale_order_line_id.product_uom_qty
            if not repair.product_id:
                continue

            if repair.product_id.product_tmpl_id.tracking != 'none' and not repair.lot_id:
                raise ValidationError(_(
                    "Serial number is required for product to repair : %s",
                    repair.product_id.display_name
                ))

            # Try to create move with the appropriate owner
            owner_id = False
            available_qty_owner = self.env['stock.quant']._get_available_quantity(repair.product_id,
                                                                                  repair.product_loct_id,
                                                                                  repair.lot_id,
                                                                                  owner_id=repair.partner_id,
                                                                                  strict=True)
            if float_compare(available_qty_owner, repair.product_qty, precision_digits=precision) >= 0:
                owner_id = repair.partner_id.id
            picking_type = self.env.ref('stock.picking_type_out', raise_if_not_found=False)
            used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations', raise_if_not_found=False)
            dest_location = repair.partner_id.property_stock_customer

            if not picking_type or not used_location:
                raise UserError('Required picking type or location is missing.')

            dev_seq = self.env['ir.sequence'].next_by_code('dn.seq') or '/'
            name = f"DN_{dest_location.name}{dev_seq}"
            picking = self.env['stock.picking'].create({
                'name': name,
                'partner_id': repair.partner_id.id,
                'picking_type_id': picking_type.id,
                'location_id': used_location.id,
                'location_dest_id': dest_location.id,
                'move_type': 'direct',
                'origin': repair.name,
                'repair_id': repair.id,
                'lead_id': repair.saleorder_id.opportunity_id.id if repair.saleorder_id.opportunity_id else repair.saleorder_id.estimation_id.lead_id
            })

            product_move_vals.append({
                'name': repair.name,
                'product_id': repair.product_id.id,
                'product_uom': repair.product_uom.id or repair.product_id.uom_id.id,
                'product_uom_qty': repair.product_qty,
                'partner_id': repair.partner_id.id,
                'location_id': repair.location_id.id,
                'location_dest_id': repair.customer_location_id.id,
                'picked': True,
                'picking_id': picking.id,
                # 'picking_id': False,
                'move_line_ids': [(0, 0, {
                    'product_id': repair.product_id.id,
                    'lot_id': repair.lot_id.id,
                    'product_uom_id': repair.product_uom.id or repair.product_id.uom_id.id,
                    'quantity': repair.product_qty,
                    'package_id': False,
                    'result_package_id': False,
                    'owner_id': owner_id,
                    'location_id': repair.product_loct_id.id,
                    'company_id': repair.company_id.id,
                    'location_dest_id': repair.customer_location_id.id,
                    'consume_line_ids': [(6, 0, repair.move_ids.move_line_ids.ids)]
                })],
                'repair_id': repair.id,
                'origin': repair.name,
                'company_id': repair.company_id.id,
            })

        product_moves = self.env['stock.move'].create(product_move_vals)
        repair_move = {m.repair_id.id: m for m in product_moves}
        for repair in self:
            move_id = repair_move.get(repair.id, False)
            if move_id:
                repair.move_id = move_id
        all_moves = self.move_ids + product_moves
        all_moves._action_done(cancel_backorder=True)

        for sale_line in self.move_ids.sale_line_id:
            price_unit = sale_line.price_unit
            sale_line.write({'product_uom_qty': sale_line.qty_delivered, 'price_unit': price_unit})

        self.state = 'done'
        # self.action_delivery_note_out()
        return True

    # def action_delivery_note_out(self):
    #     for order in self:
    #         picking_type = self.env.ref('stock.picking_type_out', raise_if_not_found=False)
    #         used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations', raise_if_not_found=False)
    #         dest_location = order.partner_id.property_stock_customer
    #
    #         if not picking_type or not used_location:
    #             raise UserError('Required picking type or location is missing.')
    #
    #         dev_seq = self.env['ir.sequence'].next_by_code('dn.seq') or '/'
    #         name = f"DN_{dest_location.name}_{dev_seq}"
    #         picking = self.env['stock.picking'].create({
    #             'name': name,
    #             'partner_id': order.partner_id.id,
    #             'picking_type_id': picking_type.id,
    #             'location_id': used_location.id,
    #             'location_dest_id': dest_location.id,
    #             'move_type': 'direct',
    #             'origin': order.name,
    #             'repair_id': order.id,
    #             'lead_id': order.saleorder_id.opportunity_id.id if order.saleorder_id.opportunity_id else order.saleorder_id.estimation_id.lead_id
    #         })
    #
    #
    #         if order.product_id and order.product_qty > 0:
    #             self.env['stock.move'].create({
    #                 'name': order.product_id.name,
    #                 'description_picking': order.product_id.name,
    #                 'product_id': order.product_id.id,
    #                 'product_uom_qty': order.product_qty,
    #                 'product_uom': order.product_uom.id,
    #                 'location_id': used_location.id,
    #                 'location_dest_id': dest_location.id,
    #                 'picking_id': picking.id,
    #                 'lead_id': order.saleorder_id.opportunity_id.id if order.saleorder_id.opportunity_id else order.saleorder_id.estimation_id.lead_id
    #             })
    #
    #
    #     return True

    def action_view_delivery_note_repair(self):
        self.ensure_one()
        # outgoing_picking_ids = self.env['stock.picking'].search([('lead_id', '=', self.saleorder_id.opportunity_id.id if self.saleorder_id.opportunity_id else self.saleorder_id.estimation_id.lead_id)]).filtered(
        #     lambda p: p.picking_type_id.code == 'outgoing')
        # print(outgoing_picking_ids,"outgoing_picking_ids")

        return {
            'name': _('Detailed Operations'),
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'domain': [('repair_id', '=', self.ids)],
            'context': {
                'create': False,
                'default_pro_id': self.product_id.id,
            }
        }


    def action_jobsheet(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Job sheet',
            'view_mode': 'tree,form',
            'res_model': 'calibration.form',
            'domain': [('id', '=', self.job_ref_calibration.id)],
            'context': {'create': False}
        }

    def action_jobsheet_lsa(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Job sheet',
            'view_mode': 'tree,form',
            'res_model': 'lsa.form',
            'domain': [('id', '=', self.job_ref_lsa.id)],
            'context': {'create': False}
        }

    def action_jobsheet_ffa(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Job sheet',
            'view_mode': 'tree,form',
            'res_model': 'ffa.form',
            'domain': [('id', '=', self.job_ref_ffa.id)],
            'context': {'create': False}
        }

    def action_jobsheet_field_service(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Job sheet',
            'view_mode': 'tree,form',
            'res_model': 'field.service',
            'domain': [('id', '=', self.job_ref_field_service.id)],
            'context': {'create': False}
        }

    def action_jobsheet_nav_comm(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Job sheet',
            'view_mode': 'tree,form',
            'res_model': 'navigation.communication',
            'domain': [('id', '=', self.job_ref_nav_comm.id)],
            'context': {'create': False}
        }

    def action_view_mr(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Request',
            'view_mode': 'tree,form',
            'res_model': 'material.purchase.requisition',
            'domain': [('repair_id', '=', self.id)],
            'context': {'create': False}
        }

    def create_material_rqst(self):
        orderline = []
        add_lines = self.move_ids.filtered(lambda m: m.repair_line_type == 'add')
        if len(add_lines) == 0:
            raise ValidationError('No materials are added for requesting')
        loc = False
        self.mr_created = True
        for line in add_lines:
            loc = line.location_id.id
            line_vals = (0, 0, {
                'product_id': line.product_id.id,
                'description': line.product_id.name,
                'qty': line.product_uom_qty,
                'uom_id': line.product_id.uom_id.id,
            })
            orderline.append(line_vals)
        emp = self.env['hr.employee'].search([('name', '=', self.user_id.partner_id.name)])
        if len(emp) == 0:
            raise ValidationError("There is no employee linked with this user:" + self.user_id.partner_id.name)
        elif not emp.department_id:
            raise ValidationError("Add department for :" + self.user_id.partner_id.name)
        vals = {

            'employee_id': emp.id,
            'department_id': emp.department_id.id,
            'department_res_id': emp.department_id.id,
            'requisition_line_ids': orderline,
            'issue_against': 'location',
            'issue_location': loc,
            'repair_id': self.id,
            'so_id': self.saleorder_id.id
        }
        mr_id = self.env['material.purchase.requisition'].create(vals)
        for user in self.env['res.users'].search([]):
            if user.has_group('stock.group_stock_multi_locations'):
                mr_id.activity_schedule('kg_jobsheet.material_req_notification',
                                        user_id=user.id,
                                        note=f' The User {self.env.user.name} created a material request. Please Verify and allocate the materials.')

    def action_repair_end(self):
        if not self.move_ids:
            res = super(RepairOrder, self).action_repair_end()
            self.state = 'calibrated'
            sale_order = self.saleorder_id
            existing_line = sale_order.order_line.filtered(lambda l: l.product_id == self.product_id)
            if existing_line:
                sale_qty = existing_line.product_uom_qty
                repair_qty = self.product_qty
                existing_line.qty_delivered += repair_qty
                existing_line.balance_qty = sale_qty - repair_qty
            return res

        else:
            if any(not li.quantity for li in self.move_ids):
                raise ValidationError("Quantity is required. Please update the quantity before completing the repair.")
            res = super(RepairOrder, self).action_repair_end()
            if self.is_calibration_repair and self.saleorder_id:
                sale_order = self.saleorder_id
                existing_line = sale_order.order_line.filtered(lambda l: l.product_id == self.product_id)
                if existing_line:
                    sale_qty = existing_line.product_uom_qty
                    repair_qty = self.product_qty
                    existing_line.qty_delivered += repair_qty
                    existing_line.balance_qty = sale_qty - repair_qty

                message = "Repair completed: Updated delivery quantities for products."
                sale_order.message_post(body=message)
                self.message_post(body=message)

            return res

    def create_final_certificate(self):
        return self.env.ref("kg_jobsheet.action_final_calibration_dimension_report").report_action(self)

    def create_final_certificate_lsa(self):
        return self.env.ref("kg_jobsheet.action_final_lsa_certificate").report_action(self)

    def create_final_certificate_ffa(self):
        return self.env.ref("kg_jobsheet.action_final_ffa_certificate").report_action(self)

    def create_final_certificate_field_service(self):
        return self.env.ref("kg_jobsheet.action_final_certificate_field_service").report_action(self)

    def create_final_certificate_nav_com(self):
        return self.env.ref("kg_jobsheet.action_final_certificate_navi_communication").report_action(self)


class MaterialPurchaseRequisition(models.Model):
    _inherit = "material.purchase.requisition"

    repair_id = fields.Many2one('repair.order')
