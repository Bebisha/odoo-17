from odoo import models, fields, api


class InspectionReport(models.Model):
    _name = "inspection.report"
    _description = "Inspection Report"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'inspect_no'

    name = fields.Char(string="Reference", copy=False)
    inspection_content_view = fields.Html(string="Inspection Content")
    lead_id = fields.Many2one("crm.lead", string="Opportunity")
    partner_id = fields.Many2one("res.partner", string="Client Name")
    vessel_id = fields.Many2one("vessel.code", string="Vessel")
    date = fields.Date(string="Date")
    location = fields.Char(string="Location")
    enq_no = fields.Char(string="Enquiry No", related="lead_id.enq_no")
    inspect_no = fields.Char(string="Inspection No", related="lead_id.inspect_no")
    service_equipment_ids = fields.Many2many("product.product", string="Service Instruments",
                                             compute="compute_products")
    equipment_id = fields.Many2one("product.product", string="Equipment",
                                   domain="[('id', 'in', service_equipment_ids)]")

    @api.depends('lead_id')
    def compute_products(self):
        for rec in self:
            products = rec.lead_id.inspection_cal_ids.mapped('pro_id').ids
            rec.service_equipment_ids = [(6, 0, products)]

    make_id = fields.Many2one('rec.make', string='Make')
    model_id = fields.Many2one('rec.model', string='Model')
    model_no = fields.Char(string="Model No")
    serial_no = fields.Char(string="Serial No")

    is_supply = fields.Boolean(string="Supply", default=False)
    is_maintenance = fields.Boolean(string="Maintenance", default=False)
    is_new_installation = fields.Boolean(string="New Installation", default=False)
    testing_certificate = fields.Boolean(string="Testing Certificate", default=False)

    work_description = fields.Html(string="Work Description")
    findings = fields.Html(string="Findings")
    re_medical_action = fields.Html(string="Remedial Action")

    inspection_report_line_ids = fields.One2many("inspection.report.line", 'inspection_report_id',
                                                 string="Spares Required")

    condition_report_line_ids = fields.One2many("condition.report.line", 'inspection_report_id',
                                                string="Spares Required")

    is_hotwork_permit = fields.Boolean(string="Hotwork Permit", default=False)
    is_scafolding = fields.Boolean(string="Scafolding", default=False)
    is_craneage = fields.Boolean(string="Craneage", default=False)
    is_ventilation = fields.Boolean(string="Ventilation", default=False)
    is_outfit_removal = fields.Boolean(string="Outfit Removal", default=False)
    is_lifting = fields.Boolean(string="Lifting", default=False)
    is_transportation = fields.Boolean(string="Transportation", default=False)
    is_requirement_other = fields.Boolean(string="Other", default=False)

    is_drawings = fields.Boolean(string="Drawings", default=False)
    is_sample = fields.Boolean(string="Sample", default=False)
    is_photograph = fields.Boolean(string="Photograph", default=False)
    is_document_other = fields.Boolean(string="Other", default=False)

    inspected_by = fields.Many2one('res.users', string="Inspected By", readonly=True)
    verified_by = fields.Many2one('res.users', string="Verified By", readonly=True)
    inspected_signature = fields.Binary(string="Inspected By")
    verified_signature = fields.Binary(string="Verified By,")
    general_requirement = fields.Text(string="General Requirement")
    documents_available = fields.Text(string="Documents Available")

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    seq_lot_line_ids = fields.One2many(
        'inspection.report.lot.line',
        'inspection_report_id',
        string="Service instrument details",
    )

    def get_file_name_from_folder(self):
        folder = self.env.ref('kg_voyage_marine_crm.document_inspection_form_folder')
        if not folder:
            return ''
        doc = self.env['documents.document'].search([('folder_id', '=', folder.id)], limit=1)
        return doc.name

    @api.onchange('inspected_signature')
    def onchange_inspected_signature(self):
        if self.inspected_signature:
            self.inspected_by = self.env.user.id
        else:
            self.inspected_by = False

    @api.onchange('verified_signature')
    def onchange_verified_signature(self):
        if self.verified_signature:
            self.verified_by = self.env.user.id
        else:
            self.verified_by = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('inspection.report.seq')
        return super(InspectionReport, self).create(vals_list)

    @api.onchange('lead_id')
    def get_enquiry_details(self):
        for rec in self:
            if rec.lead_id:
                rec.partner_id = rec.lead_id.partner_id.id
                rec.vessel_id = rec.lead_id.vessel_id.id

            else:
                rec.partner_id = False
                rec.vessel_id = False
                rec.equipment_id = False

    @api.onchange('inspection_report_line_ids')
    def _onchange_update_serial_numbers(self):
        if self.inspection_report_line_ids:
            for idx, line in enumerate(self.inspection_report_line_ids, start=1):
                line.sl_no = idx

    def _prepare_lot_lines(self):
        """Prepare lot lines for report based on available internal stock"""
        self.ensure_one()

        if not self.service_equipment_ids or not self.lead_id:
            return []

        StockQuant = self.env['stock.quant']
        product_tmpl_ids = self.service_equipment_ids.mapped('product_tmpl_id').ids

        quants = StockQuant.search([
            ('product_id.product_tmpl_id', 'in', product_tmpl_ids),
            ('lead_id', '=', self.lead_id.id),
            ('lot_id', '!=', False),
            ('quantity', '>', 0),
            ('location_id.usage', 'in', ('internal', 'inventory')),
        ])

        lot_lines = []

        for quant in quants:
            lot = quant.lot_id

            lot_lines.append((0, 0, {
                'pro_id': quant.product_id.id,
                'lot_number_text': quant.lot_number_text,
                'product_category': quant.product_categ_id.id,
                'make_id': quant.make_id.id,
                'model_id': quant.model_id.id,
                'lot_id': lot.id,
                'serial_no': lot.name,
                'accesories': quant.accesories,
                'physical_status_id': quant.physical_status_id.id,
                'remark': quant.remark,
                'qty': quant.quantity,
                'lead_id': quant.lead_id.id,
                'report_remark': ''
            }))

        return lot_lines

    @api.onchange('equipment_id', 'lead_id')
    def _onchange_equipment_id(self):
        for rec in self:
            rec.seq_lot_line_ids = [(5, 0, 0)]
            rec.seq_lot_line_ids = rec._prepare_lot_lines()

    @api.model
    def create(self, vals):
        record = super().create(vals)
        print(vals, "valasssssssssssssss")
        if record.equipment_id and record.lead_id:
            record.seq_lot_line_ids = [(5, 0, 0)]
            record.seq_lot_line_ids = record._prepare_lot_lines()
        return record

    def write(self, vals):
        res = super().write(vals)
        print(vals, "valasssssssssssssss")
        for rec in self:
            if 'equipment_id' in vals or 'lead_id' in vals:
                rec.seq_lot_line_ids = [(5, 0, 0)]
                if rec.equipment_id and rec.lead_id:
                    rec.seq_lot_line_ids = rec._prepare_lot_lines()
        return res

    # @api.onchange('equipment_id')
    # def _onchange_equipment_id(self):
    #     lot_lines = []
    #     if self.equipment_id and self.lead_id:
    #         quants = self.env['stock.quant'].search([
    #             ('product_id.product_tmpl_id', '=', self.equipment_id.id),
    #             ('lead_id', '=', self.lead_id.id),
    #             ('lot_id', '!=', False),
    #         ])
    #         MoveLine = self.env['stock.move.line']
    #         for quant in quants:
    #             qty = quant.inventory_quantity_auto_apply
    #             if qty <= 0:
    #                 continue
    #             lot = quant.lot_id
    #
    #             # ---- FIND FINAL MOVE TO CHECK LOCATION ------------------
    #             moves = MoveLine.search([
    #                 ('lot_id', '=', lot.id),
    #                 ('product_id', '=', quant.product_id.id),
    #                 ('state', '=', 'done'),
    #             ], order='date, create_date')
    #
    #             if moves:
    #                 final_move = moves[-1]  # last movement
    #                 final_usage = final_move.location_dest_id.usage
    #             else:
    #                 final_usage = 'internal'  # default
    #             # ----------------------------------------------------------
    #
    #             # ❗ ALLOW ONLY INTERNAL / VIRTUAL / INVENTORY
    #             if final_usage in ('customer', 'supplier', 'inventory_loss', 'production'):
    #                 continue
    #
    #             # ---- ADD LOT -------------------------
    #             lot_lines.append((0, 0, {
    #                 'serial_no': quant.serial_no,
    #                 'pro_id': quant.product_id.id,
    #                 'lot_number_text': quant.lot_number_text,
    #                 'product_category': quant.product_categ_id.id,
    #                 'make_id': quant.make_id.id,
    #                 'model_id': quant.model_id.id,
    #                 'name': lot.name,
    #                 'lot_id': lot.id,
    #                 'accesories': quant.accesories,
    #                 'physical_status_id': quant.physical_status_id.id,
    #                 'remark': quant.remark,
    #                 'qty': qty,
    #                 'lead_id': quant.lead_id.id,
    #             }))
    #     # --------------------------------------------------------------
    #
    #     self.seq_lot_line_ids = lot_lines


class InspectionReportLine(models.Model):
    _name = "inspection.report.line"
    _description = "Inspection Report Line"

    name = fields.Char(string="Reference")
    inspection_report_id = fields.Many2one("inspection.report", string="Inspection Report")
    sl_no = fields.Integer(string="SL.No")
    description = fields.Text(string="Description")
    part_no = fields.Char(string="Part No")
    qty = fields.Float(string="Quantity")
    uom_id = fields.Many2one("uom.uom", string="Units")


class ConditionReportLine(models.Model):
    _name = "condition.report.line"
    _description = "Condition Report Line"

    inspection_report_id = fields.Many2one("inspection.report", string="Inspection Report")
    sl_no = fields.Integer(string="SL.No")
    description = fields.Text(string="System Description")
    findings = fields.Text(string="Findings")
    recommendation = fields.Text(string="Recommendation")
    spares = fields.Text(string="Spares")
    remarks = fields.Text(string="Remarks")
    image = fields.Image(string="Status Image", max_width=1024, max_height=1024, tracking=True)


class InspectionReportLotLine(models.Model):
    _name = 'inspection.report.lot.line'
    _description = 'Inspection Report Lot Line'

    inspection_report_id = fields.Many2one(
        'inspection.report',
        string="Inspection Report",
        ondelete='cascade'
    )
    sl_no = fields.Integer(
        string="SL No", compute='_compute_sl_no',
        store=False
    )
    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'), ('ft', 'FT')
    ], string="Code")

    serial_no = fields.Char(string="Serial No")
    pro_id = fields.Many2one('product.product', string="Product")
    lot_id = fields.Many2one('stock.lot', string="Lot")
    lot_number_text = fields.Char(string="Lot Number")
    product_category = fields.Many2one('product.category', string="Category")
    make_id = fields.Many2one('rec.make', string="Make")
    model_id = fields.Many2one('rec.model', string="Model")
    accesories = fields.Text(string="Accessories")
    physical_status_id = fields.Many2one('physical.status', string="Physical Status")
    remark = fields.Text(string="Remark")
    report_remark = fields.Text(string="Report Remark")
    qty = fields.Float(string="Quantity")
    lead_id = fields.Many2one('crm.lead', string="Lead")

    def _compute_sl_no(self):
        for rec in self:
            if rec.inspection_report_id:
                for index, line in enumerate(rec.inspection_report_id.seq_lot_line_ids, start=1):
                    line.sl_no = index

    # @api.model
    # def create(self, vals):
    #     records = super(InspectionReportLotLine, self).create(vals)
    #     print(vals, "records")
    #     print(records, "records")
    #
    #     for line in records:
    #         report = line.inspection_report_id
    #         remark = line.report_remark
    #         print(report, remark, "report_remark")
    #
    #         if not report or not report.lead_id or not remark:
    #             continue
    #
    #         # Update related inspection.calibration records
    #         inspection_lines = self.env['inspection.calibration'].search([
    #             ('crm_id', '=', report.lead_id.id),
    #             ('pro_id', '=', line.pro_id.id),
    #         ])
    #
    #         for insp in inspection_lines:
    #             existing = insp.remark or ''
    #             new_remark = f"• {remark}"
    #             insp.remark = f"{existing}\n{new_remark}" if existing else new_remark
    #
    #     return records

    # def write(self, vals):
    #     res = super().write(vals)
    #
    #     if 'report_remark' in vals:
    #         for line in self:
    #             if not line.report_remark:
    #                 continue
    #
    #             report = line.inspection_report_id
    #             if not report or not report.lead_id:
    #                 continue
    #
    #             inspection_lines = self.env['inspection.calibration'].search([
    #                 ('crm_id', '=', report.lead_id.id),
    #                 ('pro_id', '=', line.pro_id.id),
    #             ])
    #
    #             bullet = f"• {line.report_remark}"
    #
    #             for insp in inspection_lines:
    #                 existing = insp.remark or ''
    #                 if bullet not in existing:
    #                     insp.remark = (
    #                         f"{existing}\n{bullet}" if existing else bullet
    #                     )
    #
    #     return res
