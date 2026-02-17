from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CalibrationForm(models.Model):
    _name = 'calibration.form'
    _description = 'Calibration Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Calibration Number", copy=False, index=True, readonly=False,
                       default=lambda self: _('New'))
    vessel = fields.Char(string="Vessel")
    vessel_id = fields.Many2one('vessel.code', string='Vessel')
    scope_id = fields.Many2one('equipment.master', string="Equipment", domain="[('id', 'in', equipment_records_ids)]")
    equipment_id = fields.Many2one('equipment.category', string="Equipment Category")
    product_category_id = fields.Many2one('product.category', string="Equipment Category")
    product_category_parent_id = fields.Many2one('product.category', string="Scope")
    product_category_ids = fields.Many2many('product.category', string="Equipment Category")
    product_id = fields.Many2one('product.template', string="Product")
    customer_name = fields.Char(string="Customer")
    partner_id = fields.Many2one('res.partner', string="Customer")
    customer_address = fields.Char(string="Customer Address")
    certificate_ref = fields.Char(string="Certificate Reference")
    certificate_no = fields.Char(string="Certificate No")
    received_date = fields.Date(string="Received Date")
    calibration_date = fields.Date(string="Calibration Date")
    recommended_due_date = fields.Date(string="Recommended Due Date")
    temperature_with_accuracy = fields.Char(string="Temperature with Accuracy")
    humidity_with_accuracy = fields.Char(string="Humidity with Accuracy")
    master_equipment_make = fields.Char(string="Master Equipment Make")
    master_equipment_serial_no = fields.Char(string="Master Equipment Serial No")
    master_equipment_certificate = fields.Char(string="Master Equipment Certificate")
    master_equipment_traceability = fields.Char(string="Master Equipment Traceability")
    unit_make = fields.Char(string="Unit Make", related='product_id.make')
    unit_model = fields.Char(string="Unit Model", related='product_id.model')
    unit_serial_no = fields.Char(string="Unit Serial No")
    unit_range = fields.Float(string="Unit Range", related='product_id.product_range')
    unit_resolution = fields.Char(string="Resolution")
    unit_accuracy = fields.Char(string="Accuracy")
    test_method_variation = fields.Char(string="Test Method Variation")
    work_instruction = fields.Many2one('work.instruction', string="Work Instruction",
                                       related='product_id.work_instruction_id')
    standards = fields.Many2one('standard.used', string="Standards", related='product_id.standard_used_id')
    calibration_notes = fields.Html(string="Calibration Notes")
    calibration_remarks = fields.Text(string="Calibration Remarks")
    equipment_records_ids = fields.Many2many('product.template')
    certificate_id = fields.Many2one('certificate.master', string="Certificate")
    certificate_content_view = fields.Html(string="Certificate Content")
    make_id = fields.Many2one('rec.make', string='Make')
    model_id = fields.Many2one('rec.model', string='Model')

    saleorder_id = fields.Many2one("sale.order", string="Sale Order")
    jr_no = fields.Char('JR.No', copy=False, readonly=True, related="saleorder_id.jr_no")

    test_view = fields.Html(string="Test result")
    job_sheet_number = fields.Char(string="Jobsheet Number")
    qty_calibration = fields.Float("QTY")
    product_group_id = fields.Many2one("product.group", string="Group", related='product_id.product_group_id')
    price_unit = fields.Float(string="Unit Price")
    opportunity_id = fields.Many2one("crm.lead", string="Opportunity")

    seq_lot_ids = fields.One2many(
        'sequence.lot',
        'calibration_id',
        string='Services Instrument'
    )
    seq_lot_line_ids = fields.One2many(
        'sequence.lot.line',
        'seq_line_lot',
        string='Services Instrument' ,readonly=False
    )
    lead_id = fields.Many2one('crm.lead', string="Lead")

    # @api.depends('product_id')
    # def _compute_filtered_seq_lot_ids(self):
    #     for rec in self:
    #         rec.seq_lot_ids = self.env['sequence.lot'].search([
    #             ('pro_id', '=', rec.product_id.id)
    #         ])

    product_template_ids = fields.One2many(
        'equipment.master.line',
        'calibration_form_id',
        string='Master Equipment'
    )
    inspection_calibration_id = fields.Many2one('inspection.calibration', string="Inspection")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        lot_lines = []

        if self.product_id and self.lead_id:

            # Find all quants for this product & this lead
            quants = self.env['stock.quant'].search([
                ('product_id.product_tmpl_id', '=', self.product_id.id),
                ('lead_id', '=', self.lead_id.id),
                ('lot_id', '!=', False),
            ])

            MoveLine = self.env['stock.move.line']

            for quant in quants:

                qty = quant.inventory_quantity_auto_apply
                self.received_date = quant.create_date

                # ❗ Skip if quantity <= 0
                if qty <= 0:
                    continue

                lot = quant.lot_id

                # ---- FIND FINAL MOVE TO CHECK LOCATION ------------------
                moves = MoveLine.search([
                    ('lot_id', '=', lot.id),
                    ('product_id', '=', quant.product_id.id),
                    ('state', '=', 'done'),
                ], order='date, create_date')

                if moves:
                    final_move = moves[-1]  # last movement
                    final_usage = final_move.location_dest_id.usage
                else:
                    final_usage = 'internal'  # default
                # ----------------------------------------------------------

                # ❗ ALLOW ONLY INTERNAL / VIRTUAL / INVENTORY
                if final_usage in ('customer', 'supplier', 'inventory_loss', 'production'):
                    continue

                # ---- ADD LOT -------------------------
                lot_lines.append((0, 0, {
                    'serial_no': quant.serial_no,
                    'pro_id': quant.product_id.id,
                    'lot_number_text': quant.lot_number_text,
                    'product_category': quant.product_categ_id.id,
                    'make_id': quant.make_id.id,
                    'model_id': quant.model_id.id,
                    'name': lot.name,
                    'lot_id': lot.id,
                    'accesories': quant.accesories,
                    'physical_status_id': quant.physical_status_id.id,
                    'remark': quant.remark,
                    'qty': qty,
                    'lead_id': quant.lead_id.id,
                }))
        # --------------------------------------------------------------

        self.seq_lot_line_ids = lot_lines


        # WWWWWWWWWWWWWWW

    sale_form_count = fields.Integer(
        string="SaleOrder Count",
        compute="_compute_form_counts_sale"
    )
    repair_form_count = fields.Integer(
        string="Repair Count",
        compute="_compute_form_counts_repair"
    )

    def _compute_form_counts_sale(self):
        for order in self:
            order.sale_form_count = self.env['sale.order'].search_count([('id', '=', self.saleorder_id.id)])

    def _compute_form_counts_repair(self):
        for order in self:
            order.repair_form_count = self.env['repair.order'].search_count([('job_ref_calibration', '=', self.id)])

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('calibration.seq') or _('New')
        return super(CalibrationForm, self).create(vals)

    @api.onchange('product_category_id')
    def _onchange_product_category_id(self):
        if self.product_category_id:
            equipment_category_id = self.product_category_id.id

            equipment_records = self.env['product.template'].search(
                [('categ_id', '=', equipment_category_id)])

            self.equipment_records_ids = [(6, 0, equipment_records.ids)]

    @api.onchange('product_id')
    def _onchange_certificates_id(self):
        for record in self:
            if record.product_id:
                test_result = record.product_id.certificate_id.certificate
                certifacte_no = record.product_id.certificate_id.name
                certifacte_description = record.product_id.certificate_id.description
                record.test_view = test_result
                record.certificate_content_view = record.test_view
                record.certificate_ref = certifacte_no
                record.calibration_notes = certifacte_description

    # def create_calibration(self):
    #     if self.qty_calibration <= 0.0:
    #         raise ValidationError("The quality calibration cannot be zero or negative.")
    #
    #     existing_repair_orders = self.env['repair.order'].search([
    #         ('job_ref_calibration', '=', self.id),
    #         ('product_id', '=', self.product_id.product_variant_id.id),
    #     ])
    #     existing_qty = sum(order.product_qty for order in existing_repair_orders)
    #     if existing_qty >= self.qty_calibration:
    #         raise ValidationError(
    #             f"The existing quantity of {existing_qty} exceeds or equals the requested quantity of {self.qty_calibration}.")
    #     if existing_qty == 0:
    #         product_qty = self.qty_calibration
    #     else:
    #         product_qty = self.qty_calibration - existing_qty
    #     if product_qty <= 0:
    #         raise ValidationError("No remaining quantity available for calibration.")
    #     vessel = self.vessel_id.id
    #     job_ref_calibration = self.id
    #     product_category_id = self.product_category_id.id
    #     partner_id = self.partner_id.id
    #     product_tmpl_id = self.product_id.product_variant_id.id
    #     certificate_content_view = self.product_id.certificate_id.certificate if self.product_id and self.product_id.certificate_id else None
    #     saleorder_id = self.saleorder_id
    #     quant = self.env['stock.quant'].search([
    #         ('product_id', '=', product_tmpl_id),
    #
    #     ])
    #     print(quant, "quant")
    #     location_ids = quant.mapped('location_id.id')
    #     print(location_ids, "location_ids")
    #     product_loct_id = location_ids[0] if location_ids else False
    #
    #     repair_order = self.env['repair.order'].create({
    #         'vessel': vessel,
    #         'job_ref_calibration': job_ref_calibration,
    #         'partner_id': partner_id,
    #         'product_id': product_tmpl_id,
    #         'product_category_id': product_category_id,
    #         'certificate_content_view': certificate_content_view,
    #         'product_loct_id': product_loct_id,
    #         'saleorder_id': saleorder_id.id,
    #         'customer_location_id': self.partner_id.property_stock_customer.id,
    #         'is_calibration_repair': True,
    #         'product_qty': product_qty
    #     })
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Repair Form',
    #         'res_model': 'repair.order',
    #         'view_mode': 'form',
    #         'res_id': repair_order.id,
    #         'view_id': self.env.ref('repair.view_repair_order_form').id,
    #         'target': 'current',
    #     }

    def create_calibration(self):
        if self.qty_calibration <= 0.0:
            raise ValidationError("The quantity for calibration cannot be zero or negative.")

        # Check existing repair orders
        existing_repair_orders = self.env['repair.order'].search([
            ('job_ref_calibration', '=', self.id),
            ('product_id', '=', self.product_id.product_variant_id.id),
        ])
        existing_qty = sum(order.product_qty for order in existing_repair_orders)
        if existing_qty >= self.qty_calibration:
            raise ValidationError(
                f"The existing quantity of {existing_qty} exceeds or equals the requested quantity of {self.qty_calibration}."
            )

        remaining_qty = int(self.qty_calibration - existing_qty)
        if remaining_qty <= 0:
            raise ValidationError("No remaining quantity available for calibration.")

        # Common info
        product_tmpl_id = self.product_id.product_variant_id.id
        vessel = self.vessel_id.id
        product_category_id = self.product_category_id.id
        partner_id = self.partner_id.id
        saleorder_id = self.saleorder_id.id
        customer_location = self.partner_id.property_stock_customer.id
        certificate_content_view = (
            self.product_id.certificate_id.certificate
            if self.product_id and self.product_id.certificate_id
            else None
        )
        used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations')
        location_id = used_location.id

        # Fetch available stock.quants
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product_tmpl_id),
            ('location_id', '=', location_id),
            ('lot_id', '!=', False),
            ('quantity', '>', 0),
        ])
        available_quants = quants.sorted(key=lambda q: q.id)

        if len(available_quants) < remaining_qty:
            lot_names = ', '.join(available_quants.mapped('lot_id.name'))
            found_count = len(available_quants)
            raise ValidationError(_(
                f"Not enough serial numbers available in the used location.\n"
                f"Found only {found_count}: {lot_names} — required {remaining_qty}."
            ))
        created_orders = []

        # Case 1: seq_lot_line_ids present
        if self.seq_lot_line_ids:
            selected_lines = self.seq_lot_line_ids.filtered(lambda l: l.x_check_done and not l.is_already_created)
            if not selected_lines:
                raise UserError("All selected lines have already been used to create repair orders.")
            for line in selected_lines:
                repair_order = self.env['repair.order'].create({
                    'vessel_id': self.vessel_id.id,
                    'job_ref_calibration': self.id,
                    'partner_id': partner_id,
                    'product_id': product_tmpl_id,
                    'product_category_id': product_category_id,
                    'certificate_content_view': certificate_content_view,
                    'product_loct_id': location_id,
                    'lot_id': line.lot_id.id,
                    'make_id': line.make_id.id,
                    'model_id': line.model_id.id,
                    'accesories': line.accesories,
                    'physical_status_id': line.physical_status_id.id,
                    'remark': line.remark,
                    'saleorder_id': saleorder_id,
                    'customer_location_id': customer_location,
                    'is_calibration_repair': True,
                    'product_qty': 1.0,
                })
                created_orders.append(repair_order.id)
                line.is_already_created = True

        else:
            # Case 2: no lines selected, use available stock.quants
            for i in range(remaining_qty):
                quant = available_quants[i]
                lot_id = quant.lot_id.id

                repair_order = self.env['repair.order'].create({
                    'vessel_id': self.vessel_id.id,
                    'job_ref_calibration': self.id,
                    'partner_id': partner_id,
                    'product_id': product_tmpl_id,
                    'product_category_id': product_category_id,
                    'certificate_content_view': certificate_content_view,
                    'product_loct_id': location_id,
                    'lot_id': lot_id,
                    'saleorder_id': saleorder_id,
                    'customer_location_id': customer_location,
                    'is_calibration_repair': True,
                    'product_qty': 1.0,
                })
                created_orders.append(repair_order.id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Calibration Repairs',
            'res_model': 'repair.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_orders)],
            'target': 'current',
        }

    def action_calibration(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Calibration',
            'view_mode': 'tree,form',
            'res_model': 'repair.order',
            'domain': [('job_ref_calibration', '=', self.id)],
            'context': {'create': False}
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

    def create_certificate(self):
        return self.env.ref("kg_jobsheet.action_calibration_dimension_report").report_action(self)


class EquipmentMasterline(models.Model):
    _name = 'equipment.master.line'

    calibration_form_id = fields.Many2one('calibration.form', string="Calibration Form")
    product_id = fields.Many2one('product.template', 'Product', domain="[('is_master_equipment', '=', True)]")
    equipment_make = fields.Char(string='Make', related='product_id.equipment_make')
    equipment_serial_no = fields.Char(string='Serial Number', related='product_id.equipment_serial_no')
    equipment_certificate_no = fields.Char(string='Certificate Number', related='product_id.equipment_certificate_no')
    equipment_traceability = fields.Char(string='Traceability', related='product_id.equipment_traceability')
