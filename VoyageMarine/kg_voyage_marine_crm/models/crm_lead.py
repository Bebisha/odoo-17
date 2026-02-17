from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _


class KGCRMLeadInherit(models.Model):
    _inherit = "crm.lead"

    def _get_employeed(self):
        user = self.env['res.users'].browse(self.env.uid)
        employee_id = False
        if user:
            employee_id = user.employee_id or False
        return employee_id


    enquiry_type = fields.Selection(
        [('project', 'Project'), ('service', 'Service'), ('trade', 'Trading')], string='Enquiry Type',
        default="service", copy=False)
    estimation = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                  string='Estimation', default='no', copy=False)
    inspection = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                  string='Inspection', default='yes', copy=False)
    inspection_user_ids = fields.Many2many("res.users", string='Inspection Assignees', column1='inspection_id')
    inspection_status = fields.Selection([('success', 'Approved'), ('fail', 'Rejected')], copy=False,
                                         string='Inspected Status')
    estimation_created = fields.Boolean(default=False, string="Estimation Created", copy=False)

    estimation_id = fields.Many2one("crm.estimation", string="Estimation Reference", copy=False)
    emp_id = fields.Many2one("hr.employee", readonly=False, string="Assigned To")
    estimation_type = fields.Many2many("crm.estimation", string="Choose Estimation Type", copy=False)
    po_ids = fields.Many2many("purchase.order", string="Purchase Reference", copy=False)
    rfq_ids = fields.Many2many("purchase.order",'rfq_ids_rel' ,string="Purchase Reference", copy=False)
    vessel_id = fields.Many2one('vessel.code', string='Vessel')
    employee_id = fields.Many2one("hr.employee", string="Assigned To", default=_get_employeed)
    enquiry_ref = fields.Text(string="Enquiry Reference")
    enquiry_id = fields.Many2one('enquiry.reference', string="Enquiry Reference")
    customer_ref = fields.Text(string="Customer Reference", copy=False)
    attn = fields.Char(string="Attn")
    bid_closing_date = fields.Date(string='Bid Closing Date', default=fields.Date.today())
    is_reject_inspection = fields.Boolean(default=False, copy=False)
    is_approval_inspection = fields.Boolean(default=False, copy=False)
    is_fully_available = fields.Boolean(default=False, copy=False)
    is_inspection_request_send = fields.Boolean(default=False, copy=False)
    inspect_comments = fields.Text(string="Inspect Notes")
    inspect_no = fields.Char('Inspection Number', copy=False, index=True, readonly=True, default='')
    enq_no = fields.Char('Enquiry Number', copy=False, index=True, readonly=True, default='')
    jr_no = fields.Char('JR.No', copy=False, index=True, readonly=True, default='')
    product_temp_ids = fields.One2many('product.template', 'lead_id', string='Services')
    inspection_cal_ids = fields.One2many('inspection.calibration', 'crm_id', string='Services')
    job_delivery_note = fields.Char(string="Delivery Note", copy=False, index=True, readonly=False,
                                    default=lambda self: _('New'))

    sml_ids = fields.Many2many("stock.move.line", string="Inspection", compute="compute_sml_ids")

    inspection_content_view = fields.Html(string="Inspection Content")
    inspection_report_id = fields.Many2one("inspection.report", string="Inspection Report")
    inspection_report_count = fields.Integer(string="Inspection report Count", compute="compute_count_insp_report")

    po_count = fields.Integer(string="Estimated PO Count",copy=False, compute="compute_po_ids",)
    rfq_count = fields.Integer(string="Estimated RFQ Count",copy=False, compute="compute_rfq_ids",)
    est_po_ids = fields.Many2many("purchase.order", 'est_ids_rell', 'est_po_rel', string="Enquiry PO Ref",copy=False,
                                  compute="compute_est_po_ids" )

    def get_file_name_from_folder(self):
        folder = self.env.ref('kg_voyage_marine_crm.document_inspection_form_folder')
        if not folder:
            return ''
        doc = self.env['documents.document'].search([('folder_id', '=', folder.id)], limit=1)
        return doc.name

    def compute_est_po_ids(self):
        for rec in self:
            est_ids = self.env['crm.estimation'].search([('lead_id', '=', rec.id)])
            if est_ids and est_ids.est_po_ids:
                rec.est_po_ids = est_ids.mapped('est_po_ids')
            else:
                rec.est_po_ids =  rec.po_ids | rec.rfq_ids

    @api.onchange('inspection_cal_ids')
    def _onchange_line_numberss(self):
        for rec in self:
            count = 1
            for line in rec.inspection_cal_ids:
                line.sl_no = str(count)
                count += 1

    def compute_po_ids(self):
        print("hhhhhhhhhhhhhhhh")
        for rec in self:
            rec.po_ids = rec.est_po_ids.filtered(lambda po: po.state == 'purchase') | rec.po_ids.filtered(lambda po: po.state == 'purchase')
            rec.po_count = len(rec.po_ids)

    def compute_rfq_ids(self):
        print("hhhhhhhhhhhhhhhh")
        for rec in self:
            rec.rfq_ids = rec.est_po_ids.filtered(lambda po: po.state != 'purchase') | rec.rfq_ids.filtered(lambda po: po.state != 'purchase')
            rec.rfq_count = len(rec.rfq_ids)


    def compute_count_insp_report(self):
        for rec in self:
            rec.inspection_report_count = 0
            inspection_report_id = self.env['inspection.report'].search([('lead_id', '=', rec.id)])
            if inspection_report_id:
                rec.inspection_report_count = len(inspection_report_id)
            else:
                rec.inspection_report_count = 0

    @api.onchange('inspection_report_id')
    def show_inspection_report(self):
        for rec in self:
            if rec.inspection_report_id and rec.inspection_report_id.inspection_content_view:
                rec.inspection_content_view = rec.inspection_report_id.inspection_content_view
            else:
                rec.inspection_content_view = False

    def compute_sml_ids(self):
        for rec in self:
            rec.sml_ids = False
            picking_ids = self.env['stock.picking'].search([('lead_id', '=', rec.id)])
            for picking in picking_ids:
                rec.sml_ids |= picking.move_line_ids

    @api.model
    def create(self, vals):
        enq_no_seq = self.env['ir.sequence'].next_by_code('enq.seq') or ''
        vals['enq_no'] = enq_no_seq

        return super(KGCRMLeadInherit, self).create(vals)

    is_service_instrument = fields.Boolean(string="IS Service Instrument", copy=False, default=False)
    picking_ids = fields.One2many(
        'stock.picking',
        'lead_id',
        string="Deliveries"
    )


    # def action_delivery_note(self):
    #     if not self.inspection_cal_ids:
    #         raise ValidationError("Empty Service Instruments: Add items to continue !!")
    #     if self.is_service_instrument:
    #         raise UserError("Already created service instrument")
    #     valid_lines = self.inspection_cal_ids.filtered(
    #         lambda l: l.pro_id.is_equipment
    #                   and l.pro_id.product_group_id == self.env.ref(
    #             'kg_voyage_marine_inventory.group_cal_categ_system'
    #         )
    #     )
    #     # After creating picking and stock moves
    #
    #
    #     if not valid_lines:
    #         raise ValidationError(
    #             "At least one service instrument with scope 'Calibration' and equipment must be added!"
    #         )
    #
    #     for order in self:
    #
    #         picking_type = self.env.ref('kg_voyage_marine_crm.virtual_service_receipts', raise_if_not_found=False)
    #         used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations', raise_if_not_found=False)
    #         dest_location = order.partner_id.property_stock_customer
    #
    #         if not picking_type or not used_location:
    #             raise UserError('Required picking type or location is missing.')
    #
    #         dev_seq = self.env['ir.sequence'].next_by_code('do.seq') or '/'
    #
    #         # name = f"DN_{used_location.name}{dev_seq}"
    #         # self.job_delivery_note = name
    #
    #         picking = self.env['stock.picking'].create({
    #             # 'name': name,
    #             'partner_id': order.partner_id.id,
    #             'picking_type_id': picking_type.id,
    #             'location_id': dest_location.id,
    #             'location_dest_id': used_location.id,
    #             'virtual_location_id': used_location.id,
    #             'move_type': 'direct',
    #             'origin': order.enq_no,
    #             'lead_id': order.id,
    #             'vessel_id': order.vessel_id.id,
    #             'customer_ref': order.customer_ref
    #         })
    #
    #         for line in order.inspection_cal_ids:
    #             if line.pro_id and line.qty > 0:
    #                 move = self.env['stock.move'].create({
    #                     'name': line.pro_id.name,
    #                     'description_picking': line.pro_id.name,
    #                     'product_id': line.pro_id.id,
    #                     'product_uom_qty': line.qty,
    #                     'product_uom': line.uom_id.id,
    #                     'location_id': dest_location.id,
    #                     'location_dest_id': picking.location_dest_id.id,
    #                     'picking_id': picking.id,
    #                     'lead_id': order.id
    #                 })
    #
    #                 line.write({
    #                     'picking_id': picking.id,
    #                     'stock_move_id': move.id
    #                 })
    #         self.job_delivery_note = picking.name
    #         self.is_service_instrument = True
    #         self.inspection_cal_ids.write({
    #             'is_quant_created': True
    #         })
    #         jr_no_seq = self.env['ir.sequence'].next_by_code('jr.seq') or ''
    #         division_record = self.division_id
    #         division_name = division_record.division
    #         first_letter = division_name[0].upper() if division_name else ''
    #         jr_no = f"JRN_{first_letter}{jr_no_seq}"
    #         self.jr_no = jr_no
    #
    #     return True

    def _get_last_picking(self):
        self.ensure_one()

        return self.env['stock.picking'].search(
            [('lead_id', '=', self.id)],
            order='id desc',
            limit=1
        )

    def _generate_jrn_no(self):
        self.ensure_one()
        if self.jr_no:
            return  # already generated

        seq = self.env['ir.sequence'].next_by_code('jr.seq') or ''
        division = self.division_id.division or ''
        first_letter = division[0].upper() if division else ''
        self.jr_no = f"JRN_{first_letter}{seq}"

    def action_delivery_note(self):
        if not self.inspection_cal_ids:
            raise ValidationError(_("Empty Service Instruments"))

        # Only NEW lines
        pending_lines = self.inspection_cal_ids.filtered(
            lambda l: not l.is_quant_created and l.pro_id and l.qty > 0
        )

        if not pending_lines:
            raise UserError(_("No new instruments to process"))

        valid_lines = pending_lines.filtered(
            lambda l: l.pro_id.is_equipment
                      and l.pro_id.product_group_id == self.env.ref(
                'kg_voyage_marine_inventory.group_cal_categ_system'
            )
        )

        if not valid_lines:
            raise ValidationError(
                _("At least one calibration equipment is required")
            )

        picking_type = self.env.ref(
            'kg_voyage_marine_crm.virtual_service_receipts',
            raise_if_not_found=False
        )
        used_location = self.env.ref(
            'kg_jobsheet.kg_jobsheet_used_locations',
            raise_if_not_found=False
        )

        for order in self:
            last_picking = order._get_last_picking()
            if last_picking and last_picking.state in ('draft', 'confirmed', 'assigned'):
                picking = last_picking
            else:
                if not last_picking:
                    order._generate_jrn_no()
                picking = self.env['stock.picking'].create({
                    'partner_id': order.partner_id.id,
                    'picking_type_id': picking_type.id,
                    'location_id': order.partner_id.property_stock_customer.id,
                    'location_dest_id': used_location.id,
                    # 'virtual_location_id': used_location.id,
                    'move_type': 'direct',
                    'origin': order.enq_no,
                    'lead_id': order.id,
                    'vessel_id': order.vessel_id.id,
                    'customer_ref': order.customer_ref,
                })
            for line in pending_lines:
                move = self.env['stock.move'].create({
                    'name': line.pro_id.name,
                    'description_picking': line.pro_id.name,
                    'product_id': line.pro_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.uom_id.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'picking_id': picking.id,
                    'lead_id': order.id,
                })

                line.write({
                    'picking_id': picking.id,
                    'stock_move_id': move.id,
                    'is_quant_created': True,
                })

            order.job_delivery_note = picking.name


        return True

    def action_view_delivery_note(self):
        self.ensure_one()
        return {
            'name': _('Detailed Operations'),
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'domain': [('lead_id', '=', self.id), ('repair_id', '=', False)],
            'context': {
                'create': False,
                'default_pro_id': self.inspection_cal_ids[:1].pro_id.id if self.inspection_cal_ids else False,
            }
        }

    def action_preview_job_note(self):
        return {
            'target': 'new',
            'type': 'ir.actions.act_url',
            'url': '/report/pdf/kg_voyage_marine_crm.action_job_receipt_report/%s' % self.id
        }

    @api.constrains('customer_ref')
    def _check_customer_ref_unique(self):
        for record in self:
            if record.customer_ref:
                existing_record = self.search([('customer_ref', '=', record.customer_ref), ('id', '!=', record.id)],
                                              limit=1)
                if existing_record:
                    raise ValidationError("The Customer Reference must be unique. This one already exists.")

    def write(self, vals):
        res = super(KGCRMLeadInherit, self).write(vals)
        if vals.get('employee_id'):
            employee_id = self.env['hr.employee'].search([('id', '=', vals.get(('employee_id')))], limit=1)
            if employee_id.id != self.env.user.employee_id.id:
                body = "You have been assigned to the Lead/Opportunity '%s'." % (self.name)
                self.message_post(body=body, partner_ids=[employee_id.work_contact_id.id])
        return res

    def get_rfq_ids(self):
        return {
            'name': 'Purchase Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.rfq_ids.ids),('state', '!=', 'purchase')],
            'target': 'current',
            'context': {'create': False}
        }

    def get_po_ids(self):
        return {
            'name': 'Purchase Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.po_ids.ids),('state', '=', 'purchase')],
            'target': 'current',
            'context': {'create': False}
        }

    def open_rfq_wizard(self):
        return {
            'name': 'Create RFQ',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'kg.create.rfq.wizard',
            'target': 'new',
            'context': {
                'default_opportunity_id': self.id,
            }
        }

    def create_inspection_report(self):
        inspections = self.env['inspection.calibration'].search([
            ('crm_id', '=', self.id),
        ])
        print(inspections,"inspections")
        equipment_id = inspections[:1].pro_id.id if inspections else False
        print(equipment_id,"equipment_id")
        return {
            'name': 'Create Inspection Report',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'inspection.report',
            'target': 'current',
            'context': {
                'default_lead_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_vessel_id': self.vessel_id.id,
                'default_equipment_id': equipment_id,
                # 'default_inspection_calibration_ids': [(6, 0, self.inspection_cal_ids.ids)],
                'create': True
            }
        }

    def action_view_inspection_report(self):
        return {
            'name': _('Inspection Reports'),
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'res_model': 'inspection.report',
            'domain': [('lead_id', '=', self.id)]
        }

    @api.onchange('partner_id')
    def auto_upload_salesperson(self):

        for rec in self:
            if rec.partner_id and rec.partner_id.user_id:
                rec.user_id = rec.partner_id.user_id.id

    def send_inspection_request(self):
        # if not self.inspection_cal_ids and self.inspection == 'yes':
        #     raise ValidationError(_("Please Select Inspection Product"))

        inspection_approval_user = self.inspection_user_ids.ids
        if not inspection_approval_user:
            raise ValidationError(_("Please Select Inspection Approval users"))
        inspection_users = self.env['res.users'].browse(inspection_approval_user)
        self.is_inspection_request_send = True

        self._action_schedule_activities(inspection_users)

    def _action_schedule_activities(self, inspection_users):
        records = []

        for user in inspection_users:
            record = self.activity_schedule(
                'kg_voyage_marine_crm.inspection_users_approval_notification',
                user_id=user.id,
                note=f'The user {self.env.user.name} has requested approval for the Inspected{self.name}. Please verify and approve.'
            )
            records.append(record)

        return records

    def inspection_approval(self):
        if self.inspection_cal_ids:
            receipts = self.env['stock.picking'].search([('lead_id', '=', self.id), ('repair_id', '=', False)])
            if any(receipt.state not in ['done', 'cancel'] for receipt in receipts):
                raise ValidationError(_("Please update all quantities moved to the virtual location."))
        inspection_approval_user = self.inspection_user_ids.ids
        if not inspection_approval_user:
            raise ValidationError(_("Please Select Inspection Approval users"))
        if self.env.user.id not in inspection_approval_user:
            raise UserError(_("You have no access to Approval"))
        self.is_approval_inspection = True
        self.inspection_status = 'success'
        division_record = self.division_id
        inspec = self.env['ir.sequence'].next_by_code('inspection.seq') or _('New')
        division_name = division_record.division
        first_letter = division_name[0].upper() if division_name else ''
        inspect_no = f"INS_{first_letter}{inspec}"
        self.inspect_no = inspect_no
        inspection_users = self.env['res.users'].browse(inspection_approval_user)

        self._action_schedule_approval_activities(inspection_users)

    def _action_schedule_approval_activities(self, inspection_users):
        request_approval_activity = self.env.ref('kg_voyage_marine_crm.inspection_users_approval_notification')
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_approval_activity and l.user_id != self.env.user
        ).unlink()
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_approval_activity
        ).action_done()

        for user_id in inspection_users:
            self.activity_schedule(
                'kg_voyage_marine_crm.inspection_approved_notification',
                user_id=user_id.id,
                note=f'The user {self.env.user.name} has approved for the Inspection {self.name}.'
            )
        approved_quotation_activity = self.env.ref('kg_voyage_marine_crm.inspection_approved_notification')
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == approved_quotation_activity and l.user_id != self.env.user
        ).unlink()
        self.activity_ids.filtered(
            lambda l: l.activity_type_id == approved_quotation_activity
        ).action_done()

    def action_reject(self):
        qtn_approve_users = self.inspection_user_ids.ids
        if self.env.user.id not in qtn_approve_users:
            raise UserError(_("You have no access to reject"))
        self.is_reject_inspection = True
        self.inspection_status = 'fail'
        self._action_schedule_activities_action_reject()

    def _action_schedule_activities_action_reject(self):

        self.activity_schedule('kg_voyage_marine_crm.reject_inspection_notification',
                               user_id=self.create_uid.id,
                               note=f' The user {self.env.user.name}  has rejected the approval of the Inspection {self.name}.')

        reject_approved_activity = self.env.ref('kg_voyage_marine_crm.reject_inspection_notification')

        self.activity_ids.filtered(
            lambda l: l.activity_type_id == reject_approved_activity and l.user_id != self.env.user).unlink()

        self.activity_ids.filtered(lambda l: l.activity_type_id == reject_approved_activity).action_done()

        request_send_activity = self.env.ref('kg_voyage_marine_crm.inspection_users_approval_notification')

        self.activity_ids.filtered(
            lambda l: l.activity_type_id == request_send_activity).unlink()

    # def toggle_active(self):
    #     res = super(KGCRMLeadInherit, self).toggle_active()
    #     self.is_reject_inspection = False
    #     self.is_approval_inspection = False
    #     self.is_inspection_request_send = False
    #     self.inspection_status = ""
    #     return res

    def create_estimation(self):
        if self.inspection == 'yes' and self.inspection_status == False:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Confirm Inspection',
                'res_model': 'inspection.confirmation.wizard',
                'view_mode': 'form',
                'view_id': self.env.ref('kg_voyage_marine_crm.view_inspection_confirmation_wizard').id,
                'target': 'new',
                'context': {
                    'default_lead_id': self.id,
                }
            }

        # if self.inspection_cal_ids:
        #     for ins in self.inspection_cal_ids:
        #         if not ins.update_qty:
        #             raise ValidationError(f"Cannot reset quantity for completed inspection: {ins.pro_id.name}")
        if self.estimation == 'yes':
            if not self.partner_id:
                raise ValidationError("Please Select the Customer !!")

            description = ''
            list_item_ids = []
            list_labour_ids = []
            list_material_ids = []
            list_other_ids = []
            used_inspection_ids = set()

            if self.estimation_type:
                for estimation in self.estimation_type:
                    description = (
                        f"{self.name} - {estimation.description}"
                        if self.name and estimation.description else
                        self.name or estimation.description or ' '
                    )

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
                                    'sl_no': sub_item.sl_no,
                                }
                                self.env['crm.estimation.item'].create(sub_items)
                    if self.inspection_cal_ids:
                        for ins in self.inspection_cal_ids:
                            if ins.id in used_inspection_ids:
                                continue

                            product = ins.pro_id
                            product_name = product.name or ''
                            used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations',
                                                         raise_if_not_found=False)

                            matching_lots = self.env['stock.quant'].search([
                                ('product_id', '=', product.id), ('lead_id', '=', self.ids),
                                ('location_id', '=', used_location.id)
                            ])

                            # lots = self.env['sequence.lot'].search(
                            #     [('pro_id', '=', product.id), ('inspection_calibration_id', '=', ins.id)])
                            lot_descriptions = []

                            for lot in matching_lots:
                                make = lot.make_id.name or ''
                                model = lot.model_id.name or ''
                                serial = lot.lot_id.name or ''
                                accessories = lot.accesories or ''
                                status = lot.physical_status_id.name or ''
                                description = (
                                    f"Make: {make}, Model: {model}, Serial No: {serial}, "
                                    f"Status: {status}, Accessories: {accessories}"
                                )
                                lot_descriptions.append(description)
                            # Format with numbered lines
                            if lot_descriptions:
                                numbered_lines = '\n'.join(
                                    [f"{i + 1}. {desc}" for i, desc in enumerate(lot_descriptions)])
                                des = f"{product_name}\n{numbered_lines}"
                            else:
                                des = f"{product_name}"


                            inspect_vals = {
                                'code': ins.code,
                                'product_id': ins.pro_id.id,
                                'description': des,
                                'quantity': ins.qty,
                                'uom_id': ins.uom_id.id if ins.uom_id else False,
                                'unit_price': ins.unit_price,
                                'sl_no': ins.sl_no,
                                'inspection_calibration_id': ins.id
                            }
                            valid_codes = [c[0] for c in self.env['crm.labour.cost']._fields['code'].selection]
                            if inspect_vals['code'] not in valid_codes:
                                raise ValidationError(
                                    _("Invalid code '%s' for Labour Cost creation.") % inspect_vals['code'])
                            inspect_vals_ids = self.env['crm.labour.cost'].create(inspect_vals)
                            list_labour_ids.append(inspect_vals_ids)
                            used_inspection_ids.add(ins.id)

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
                                'sl_no': labour.sl_no,
                            }
                            valid_codes = [c[0] for c in self.env['crm.labour.cost']._fields['code'].selection]
                            if labour_vals['code'] not in valid_codes:
                                raise ValidationError(
                                    _("Invalid code '%s' for Labour Cost creation.") % labour_vals['code'])
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
                                    'is_sub_item': True,
                                    'main_product_id': labour_ids.id,
                                    'sl_no': sub_lab.sl_no,
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
                                'sl_no': material.sl_no,
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
                                    'is_sub_item': True,
                                    'main_product_id': material_ids.id,
                                    'sl_no': sub_mat.sl_no,
                                }
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
                                'sl_no': other.sl_no,
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
                                    'is_sub_item': True,
                                    'main_product_id': other_ids.id,
                                    'sl_no': sub_oth.sl_no,
                                }
                                self.env['crm.other.cost'].create(sub_others)

                first_estimation = self.estimation_type[0]
                vals = {
                    'lead_id': self.id,
                    'enquiry_no': self.enq_no,
                    'customer_ref': self.customer_ref,
                    'attn': self.attn,
                    'partner_id': self.partner_id.id,
                    'vessel_id': self.vessel_id.id,
                    'description': description,
                    'item_ids': [(6, 0, [item.id for item in list_item_ids])],
                    'labour_cost_ids': [(6, 0, [labour.id for labour in list_labour_ids])],
                    'material_cost_ids': [(6, 0, [material.id for material in list_material_ids])],
                    'other_cost_ids': [(6, 0, [other.id for other in list_other_ids])],
                    'tax_id': first_estimation.tax_id.id if first_estimation.tax_id else False,
                    'scope': first_estimation.scope,
                    'work_type_id': first_estimation.work_type_id.id if first_estimation.work_type_id else False,
                    'currency_id': first_estimation.currency_id.id if first_estimation.currency_id else False,
                    'division_id': self.division_id.id,
                }

                estimation_id = self.env['crm.estimation'].create(vals)
                estimation_id.price_list_id = estimation_id.partner_id.property_product_pricelist.id

            else:
                labour_ids = []
                if self.inspection_cal_ids:
                    for ins in self.inspection_cal_ids:
                        if ins.id in used_inspection_ids:
                            continue

                        product = ins.pro_id
                        product_name = product.name or ''
                        used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations',
                                                     raise_if_not_found=False)

                        matching_lots = self.env['stock.quant'].search([
                            ('product_id', '=', product.id), ('lead_id', '=', self.ids),
                            ('location_id', '=', used_location.id)
                        ])
                        # lots = self.env['sequence.lot'].search(
                        #     [('pro_id', '=', product.id), ('inspection_calibration_id', '=', ins.id)])
                        lot_descriptions = []

                        for lot in matching_lots:
                            make = lot.make_id.name or ''
                            model = lot.model_id.name or ''
                            serial = lot.lot_id.name or ''
                            accessories = lot.accesories or ''
                            status = lot.physical_status_id.name or ''
                            description = (
                                f"Make: {make}, Model: {model}, Serial No: {serial}, "
                                f"Status: {status}, Accessories: {accessories}"
                            )
                            lot_descriptions.append(description)
                        # Format with numbered lines
                        if lot_descriptions:
                            numbered_lines = '\n'.join(
                                [f"{i + 1}. {desc}" for i, desc in enumerate(lot_descriptions)])
                            des = f"{product_name}\n{numbered_lines}"
                        else:
                            des = f"{product_name}"

                        int_vals = {
                            'code': ins.code,
                            'product_id': ins.pro_id.id,
                            'description': des,
                            'quantity': ins.qty,
                            'uom_id': ins.uom_id.id if ins.uom_id else False,
                            'unit_price': ins.unit_price,
                            'sl_no': ins.sl_no,
                            'inspection_calibration_id': ins.id
                        }
                        valid_codes = [c[0] for c in self.env['crm.labour.cost']._fields['code'].selection]
                        if int_vals['code'] not in valid_codes:
                            raise ValidationError(
                                _("Invalid code '%s' for Labour Cost creation.") % int_vals['code'])

                        inspect_vals_ids = self.env['crm.labour.cost'].create(int_vals)
                        labour_ids.append(inspect_vals_ids.id)
                        used_inspection_ids.add(ins.id)

                    estimation_vals = {
                        'vessel_id': self.vessel_id.id,
                        'lead_id': self.id,
                        'enquiry_no': self.enq_no,
                        'customer_ref': self.customer_ref,
                        'attn': self.attn,
                        'partner_id': self.partner_id.id if self.partner_id else False,
                        'scope': self.name,
                        'description': self.name,
                        'division_id': self.division_id.id if self.division_id else False,
                        'labour_cost_ids': [(6, 0, labour_ids)],
                    }

                    estimation_id = self.env['crm.estimation'].create(estimation_vals)

                    if estimation_id.partner_id and estimation_id.partner_id.property_product_pricelist:
                        estimation_id.price_list_id = estimation_id.partner_id.property_product_pricelist.id

                else:
                    estimation_vals = {
                        'lead_id': self.id,
                        'enquiry_no': self.enq_no,
                        'customer_ref': self.customer_ref,
                        'attn': self.attn,
                        'partner_id': self.partner_id.id if self.partner_id else False,
                        'scope': self.name,
                        'description': self.name,
                        'division_id': self.division_id.id if self.division_id else False,
                        'vessel_id': self.vessel_id.id if self.vessel_id else False,

                    }

                    estimation_id = self.env['crm.estimation'].create(estimation_vals)

                    if estimation_id.partner_id and estimation_id.partner_id.property_product_pricelist:
                        estimation_id.price_list_id = estimation_id.partner_id.property_product_pricelist.id

            self.estimation_created = True
            self.estimation_id = estimation_id.id

    def force_create_estimation(self):
        if self.inspection_cal_ids:
            for ins in self.inspection_cal_ids:
                if not ins.update_qty:
                    raise ValidationError(f"Cannot reset quantity for completed inspection: {ins.pro_id.name}")
        if self.estimation == 'yes':
            if not self.partner_id:
                raise ValidationError("Please Select the Customer !!")

            description = ''
            list_item_ids = []
            list_labour_ids = []
            list_material_ids = []
            list_other_ids = []
            used_inspection_ids = set()

            if self.estimation_type:
                for estimation in self.estimation_type:
                    # description = (
                    #     f"{self.name} - {self.description}"
                    #     if self.name and estimation.description else
                    #     self.name or estimation.description or ' '
                    # )

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
                                    'sl_no': sub_item.sl_no,
                                }
                                self.env['crm.estimation.item'].create(sub_items)

                    if self.inspection_cal_ids:
                        for ins in self.inspection_cal_ids:
                            if ins.id in used_inspection_ids:
                                continue

                            product = ins.pro_id
                            product_name = product.name or ''
                            used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations',
                                                         raise_if_not_found=False)

                            matching_lots = self.env['stock.quant'].search([
                                ('product_id', '=', product.id), ('lead_id', '=', self.ids),
                                ('location_id', '=', used_location.id)
                            ])
                            lot_descriptions = []
                            for lot in matching_lots:
                                make = lot.make_id.name or ''
                                model = lot.model_id.name or ''
                                serial = lot.lot_id.name or ''
                                accessories = lot.accesories or ''
                                status = lot.physical_status_id.name or ''
                                description = (
                                    f"Make: {make}, Model: {model}, Serial No: {serial}, "
                                    f"Status: {status}, Accessories: {accessories}"
                                )
                                lot_descriptions.append(description)

                            if lot_descriptions:
                                numbered_lines = '\n'.join(
                                    [f"{i + 1}. {desc}" for i, desc in enumerate(lot_descriptions)])
                                des = f"{product_name}\n{numbered_lines}"
                            else:
                                des = f"{product_name}"

                            inspect_vals = {
                                'code': ins.code,
                                'product_id': ins.pro_id.id,
                                'description': ins.lot_number_text,
                                'quantity': ins.update_qty,
                                'uom_id': ins.uom_id.id if ins.uom_id else False,
                                'unit_price': ins.unit_price,
                                'sl_no': ins.sl_no,
                                'inspection_calibration_id': ins.id
                            }

                            # ✅ Fix: validate code before creating to avoid ValueError
                            valid_codes = [c[0] for c in self.env['crm.labour.cost']._fields['code'].selection]
                            if inspect_vals['code'] not in valid_codes:
                                raise ValidationError(
                                    _("Invalid code '%s' for Labour Cost creation.") % inspect_vals['code']
                                )

                            inspect_vals_ids = self.env['crm.labour.cost'].create(inspect_vals)
                            list_labour_ids.append(inspect_vals_ids)
                            used_inspection_ids.add(ins.id)

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
                                'sl_no': labour.sl_no,
                            }

                            # ✅ Fix: validate code before create
                            valid_codes = [c[0] for c in self.env['crm.labour.cost']._fields['code'].selection]
                            if labour_vals['code'] not in valid_codes:
                                raise ValidationError(
                                    _("Invalid code '%s' for Labour Cost creation.") % labour_vals['code']
                                )

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
                                    'is_sub_item': True,
                                    'main_product_id': labour_ids.id,
                                    'sl_no': sub_lab.sl_no,
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
                                'sl_no': material.sl_no,
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
                                    'is_sub_item': True,
                                    'main_product_id': material_ids.id,
                                    'sl_no': sub_mat.sl_no,
                                }
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
                                'sl_no': other.sl_no,
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
                                    'is_sub_item': True,
                                    'main_product_id': other_ids.id,
                                    'sl_no': sub_oth.sl_no,
                                }
                                self.env['crm.other.cost'].create(sub_others)

                first_estimation = self.estimation_type[0]
                vals = {
                    'lead_id': self.id,
                    'enquiry_no': self.enq_no,
                    'customer_ref': self.customer_ref,
                    'attn': self.attn,
                    'partner_id': self.partner_id.id,
                    'vessel_id': self.vessel_id.id,
                    'description': f"{self.enq_no} - {self.name}",
                    'item_ids': [(6, 0, [item.id for item in list_item_ids])],
                    'labour_cost_ids': [(6, 0, [labour.id for labour in list_labour_ids])],
                    'material_cost_ids': [(6, 0, [material.id for material in list_material_ids])],
                    'other_cost_ids': [(6, 0, [other.id for other in list_other_ids])],
                    'tax_id': first_estimation.tax_id.id if first_estimation.tax_id else False,
                    'scope': first_estimation.scope,
                    'work_type_id': first_estimation.work_type_id.id if first_estimation.work_type_id else False,
                    'currency_id': first_estimation.currency_id.id if first_estimation.currency_id else False,
                    'division_id': self.division_id.id,
                }

                estimation_id = self.env['crm.estimation'].create(vals)
                estimation_id.price_list_id = estimation_id.partner_id.property_product_pricelist.id

            else:
                labour_ids = []
                print("lllllllllllllllll")
                if self.inspection_cal_ids:
                    for ins in self.inspection_cal_ids:
                        if ins.id in used_inspection_ids:
                            continue

                        product = ins.pro_id
                        product_name = product.name or ''
                        used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations',
                                                     raise_if_not_found=False)

                        matching_lots = self.env['stock.quant'].search([
                            ('product_id', '=', product.id), ('lead_id', '=', self.ids),
                            ('location_id', '=', used_location.id)
                        ])
                        lot_descriptions = []
                        for lot in matching_lots:
                            make = lot.make_id.name or ''
                            model = lot.model_id.name or ''
                            serial = lot.lot_id.name or ''
                            accessories = lot.accesories or ''
                            status = lot.physical_status_id.name or ''
                            description = (
                                f"Make: {make}, Model: {model}, Serial No: {serial}, "
                                f"Status: {status}, Accessories: {accessories}"
                            )
                            lot_descriptions.append(description)

                        if lot_descriptions:
                            numbered_lines = '\n'.join(
                                [f"{i + 1}. {desc}" for i, desc in enumerate(lot_descriptions)])
                            des = f"{product_name}\n{numbered_lines}"
                        else:
                            des = f"{product_name}"

                        int_vals = {
                            'code': ins.code,
                            'product_id': ins.pro_id.id,
                            'description': ins.lot_number_text,
                            'quantity': ins.update_qty,
                            'uom_id': ins.uom_id.id if ins.uom_id else False,
                            'unit_price': ins.unit_price,
                            'sl_no': ins.sl_no,
                            'inspection_calibration_id': ins.id
                        }
                        print(int_vals,"int_vals")

                        valid_codes = [c[0] for c in self.env['crm.labour.cost']._fields['code'].selection]
                        if int_vals['code'] not in valid_codes:
                            raise ValidationError(
                                _("Invalid code '%s' for Labour Cost creation.") % int_vals['code']
                            )

                        inspect_vals_ids = self.env['crm.labour.cost'].create(int_vals)
                        labour_ids.append(inspect_vals_ids.id)
                        used_inspection_ids.add(ins.id)

                    estimation_vals = {
                        'lead_id': self.id,
                        'enquiry_no': self.enq_no,
                        'customer_ref': self.customer_ref,
                        'attn': self.attn,
                        'partner_id': self.partner_id.id if self.partner_id else False,
                        'scope': self.name,
                        'description': self.name,
                        'division_id': self.division_id.id if self.division_id else False,
                        'vessel_id': self.vessel_id.id if self.vessel_id else False,
                        'labour_cost_ids': [(6, 0, labour_ids)],
                    }

                    estimation_id = self.env['crm.estimation'].create(estimation_vals)
                    if estimation_id.partner_id and estimation_id.partner_id.property_product_pricelist:
                        estimation_id.price_list_id = estimation_id.partner_id.property_product_pricelist.id

                else:
                    estimation_vals = {
                        'lead_id': self.id,
                        'enquiry_no': self.enq_no,
                        'customer_ref': self.customer_ref,
                        'attn': self.attn,
                        'partner_id': self.partner_id.id if self.partner_id else False,
                        'scope': self.name,
                        'description': self.name,
                        'division_id': self.division_id.id if self.division_id else False,
                        'vessel_id': self.vessel_id.id if self.vessel_id else False,
                    }

                    estimation_id = self.env['crm.estimation'].create(estimation_vals)
                    if estimation_id.partner_id and estimation_id.partner_id.property_product_pricelist:
                        estimation_id.price_list_id = estimation_id.partner_id.property_product_pricelist.id

            self.estimation_created = True
            self.estimation_id = estimation_id.id

    def get_estimation(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CRM Estimation',
            'view_mode': 'tree,form',
            'res_model': 'crm.estimation',
            'domain': [('id', '=', self.estimation_id.id)],
            'context': {'create': False}
        }

    def _prepare_opportunity_quotation_context(self):

        self.ensure_one()
        # for inspection in self.inspection_cal_ids:
        #     if inspection.qty < inspection.update_qty:
        #         raise UserError(_("Please validate the move"))

        order_lines = []



        for inspection in self.inspection_cal_ids:
            if inspection:
                if not inspection.update_qty:
                    raise ValidationError(f"Cannot reset quantity for completed inspection: {inspection.pro_id.name}")

            product = inspection.pro_id
            product_name = product.name or ''
            used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations', raise_if_not_found=False)
            matching_lots = self.env['stock.quant'].search([
                ('product_id', '=', product.id), ('lead_id', '=', self.ids),
                ('location_id', '=', used_location.id)
            ])

            # lots = self.env['sequence.lot'].search([('pro_id', '=', product.id),('inspection_calibration_id','=',inspection.id)])
            lot_descriptions = []

            for lot in matching_lots:
                make = lot.make_id.name or ''
                model = lot.model_id.name or ''
                serial = lot.lot_id.name or ''
                accessories = lot.accesories or ''
                status = lot.physical_status_id.name or ''
                description = (
                    f"Make: {make}, Model: {model}, Serial No: {serial}, "
                    f"Status: {status}, Accessories: {accessories}"
                )
                lot_descriptions.append(description)
            # Format with numbered lines
            if lot_descriptions:
                numbered_lines = '\n'.join(
                    [f"{i + 1}. {desc}" for i, desc in enumerate(lot_descriptions)])
                des = f"{product_name}\n{numbered_lines}"
            else:
                des = f"{product_name}"
            default_tax = self.env.company.account_sale_tax_id
            print(default_tax.name, "default_tax")
            order_lines.append((0, 0, {
                'sl_no': inspection.sl_no,
                'code': inspection.code,
                'product_id': inspection.pro_id.id,
                # 'tax_id': [(6, 0, inspection.pro_id.taxes_id.ids)],
                'tax_id': [(6, 0, default_tax.ids)] if default_tax else False,
                'name': inspection.lot_number_text,
                'product_uom_qty': inspection.update_qty or 1.0,
                'product_uom': inspection.uom_id.id,
                'price_unit': inspection.unit_price,
                'base_price_unit': inspection.unit_price,
                'inspection_calibration_id': inspection.id,
            }))
        # print("order_lines--->",order_lines)
        # print(err)
        quotation_context = {
            'default_opportunity_id': self.id,
            'default_order_type': self.enquiry_type,
            'default_partner_id': self.partner_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id,
            'default_tag_ids': [(6, 0, self.tag_ids.ids)],
            'default_division_id': self.division_id.id,
            'default_vessel_id': self.vessel_id.id,
            'default_customer_reference': self.customer_ref,
            'default_attn': self.attn,
            'default_fiscal_position_id': self.partner_id.property_account_position_id if self.partner_id.property_account_position_id else False,
            'default_order_line': order_lines,

        }
        if self.team_id:
            quotation_context['default_team_id'] = self.team_id.id
        if self.user_id:
            quotation_context['default_user_id'] = self.user_id.id


        # if self.inspection_cal_ids:

        return quotation_context

    # def action_new_quotation(self):
    #     action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.sale_action_quotations_new")
    #     action['context'] = self._prepare_opportunity_quotation_context()
    #     action['context']['search_default_opportunity_id'] = self.id
    #     action['context']['company_id'] = self.company_id.id
    #
    #     order_lines = []
    #     for inspection in self.inspection_cal_ids:
    #         order_lines.append((0, 0, {
    #             'name': inspection.des,
    #             'company_id': self.company_id.id,
    #             'product_id': inspection.pro_id.id,
    #             'product_uom_qty': inspection.qty or 1.0,  # default to 1 if qty not specified
    #             'product_uom': inspection.uom_id.id,  # also needs to exist
    #             'price_unit':  4,  # or whatever field you're using
    #         }))
    #
    #     if order_lines:
    #         action['context']['default_order_line'] = order_lines
    #
    #     return action

    def kg_add_subitems(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Costs',
            'view_mode': 'tree',
            'res_model': 'crm.material.cost',
            'domain': [('main_product_id', '=', self.id)],
            'context': dict(default_main_product_id=self.id,
                            default_is_sub_item=True),
            'target': 'new'
        }
