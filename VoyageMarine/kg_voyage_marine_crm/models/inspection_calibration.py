from datetime import datetime

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_compare


class KGInspectionCalibration(models.Model):
    _name = 'inspection.calibration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Inspection Request"

    crm_id = fields.Many2one('crm.lead', string="Lead")
    is_equipment_true = fields.Boolean(related="pro_id.is_equipment", string="IS equipment True", store=True)
    pro_id = fields.Many2one('product.product', string="Product", domain="[('is_equipment','=',True)]")
    product_temp_id = fields.Many2one('product.template', string="Product Template")
    make = fields.Char(string="Make", )
    make_id = fields.Many2one('rec.make', string='Make')
    model_id = fields.Many2one('rec.model', string='Model')
    serial_no = fields.Char(string="Serial number", )
    model = fields.Char(string='Model', )
    uom_id = fields.Many2one('uom.uom', related='pro_id.uom_id', string='UOM')
    # price = fields.Float('Price', required=True)
    unit_price = fields.Float(string='Unit Price')
    product_category = fields.Many2one('product.category', string="Category", related='pro_id.categ_id')
    description = fields.Text(string='Description')
    des = fields.Char(string='Description')
    physical_status_id = fields.Many2one('physical.status', string="Physical Status")
    accesories = fields.Text(string="Accessories")
    qty = fields.Float(string="Quantity", default=1.00)
    update_qty = fields.Float(string="Quantity", default=1.00)

    is_quant_created = fields.Boolean(string="Is Created", copy=False, default=False)
    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'),('ft','FT')
    ], string="Code")
    remark = fields.Text(
        string='Inspection Note',
        compute='_compute_remark',
        readonly=True
    )

    sl_no = fields.Char(string="Sl.No",)
    product_ids = fields.One2many('product.template', 'inspection_role_id', string='Services',
                                  domain=[('type', '=', 'service'), ('sale_ok', '=', True)])
    lot_number_text = fields.Text(string='Serial Numbers', compute="_compute_serial_number")
    lot_ids = fields.Many2many('stock.lot', string='Assigned Serials')
    lead_id = fields.Many2one('crm.lead', string="Lead")
    picking_id = fields.Many2one(
        'stock.picking',
        string="Delivery Note",
        copy=False
    )

    stock_move_id = fields.Many2one(
        'stock.move',
        string="Stock Move",
        copy=False
    )

    @api.depends('pro_id', 'crm_id')
    def _compute_remark(self):
        print("jjjjjjjjjjjjj")
        LotLine = self.env['inspection.report.lot.line']

        for rec in self:
            rec.remark = False

            if not rec.pro_id or not rec.crm_id:
                continue

            lot_lines = LotLine.search([
                ('pro_id', '=', rec.pro_id.id),
                ('inspection_report_id.lead_id', '=', rec.crm_id.id),
                ('report_remark', '!=', False),
            ])
            print(lot_lines,"lot_lines")

            if lot_lines:
                # merge all remarks
                rec.remark = '\n'.join(
                    f"• {l.report_remark}" for l in lot_lines if l.report_remark
                )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('is_equipment'):
            res['pro_id'] = self.env['product.product'].search([('is_equipment', '=', True)], limit=1).id
        return res

    sequence_lot_ids = fields.Many2many("sequence.lot", string="Sequence Lots", compute="compute_seq_lots")

    def compute_seq_lots(self):
        for rec in self:
            sequence_lot_ids = self.env['sequence.lot'].search([('inspection_calibration_id', '=', rec.id)])
            if sequence_lot_ids:
                rec.sequence_lot_ids = [(6, 0, sequence_lot_ids.ids)]
            else:
                rec.sequence_lot_ids = False

    @api.depends('pro_id', 'lead_id')
    def _compute_serial_number(self):
        StockLine = self.env['stock.move.line']

        # Get main used location
        used_location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations', raise_if_not_found=False)
        used_loc_id = used_location.id if used_location else False

        # Get all virtual/scrap/return/transit locations
        virtual_locs = self.env['stock.location'].search([
            ('usage', 'not in', ['inventory', 'transit', 'customer', 'supplier', 'production', 'scrap'])
        ])
        allowed_locations = set(virtual_locs.ids)
        if used_loc_id:
            allowed_locations.add(used_loc_id)

        for rec in self:
            product_name = rec.pro_id.name or ''
            lot_descriptions = []
            total_qty = 0.0

            if not rec.pro_id or not rec.crm_id:
                rec.lot_number_text = product_name
                rec.update_qty = 0
                continue

            # Fetch move lines for this lead + product
            all_moves = StockLine.search([
                ('product_id', '=', rec.pro_id.id),
                ('lead_id', '=', rec.crm_id.id),
                ('state', '=', 'done'),
                ('lot_id', '!=', False),
            ])

            # Group moves by lot
            lot_move_map = {}
            for m in all_moves:
                lot_move_map.setdefault(m.lot_id.id, []).append(m)

            usable_lots = {}

            # Determine latest movement for each lot
            for lot_id, moves in lot_move_map.items():
                moves_sorted = sorted(moves, key=lambda m: m.date or m.create_date)
                final_move = moves_sorted[-1]

                # Include lot if it ended in ANY allowed location
                if final_move.location_dest_id.id in allowed_locations:
                    usable_lots[lot_id] = final_move

            # If no usable lots
            if not usable_lots:
                rec.lot_number_text = product_name
                rec.update_qty = 0
                continue

            # Build descriptions
            for lot_id, move in usable_lots.items():
                desc = (
                    f"Make: {move.make_id.name or ''}, "
                    f"Model: {move.model_id.name or ''}, "
                    f"Serial No: {move.lot_id.name or ''}, "
                    f"Status: {move.physical_status_id.name or ''}, "
                    f"Accessories: {move.accesories or ''}"
                )
                lot_descriptions.append(desc)
                total_qty += move.qty_done

            numbered_lines = '\n'.join(
                f"{i + 1}. {line}" for i, line in enumerate(lot_descriptions)
            )

            rec.lot_number_text = f"{product_name}\n{numbered_lines}"
            rec.update_qty = total_qty

    def action_assign_serials(self):
        if self.is_quant_created:
            raise ValidationError(_("Already updated the qty"))
        if self.pro_id.tracking != 'serial':
            raise ValidationError(_("Please enable the configuration"))

        self.ensure_one()

        StockQuant = self.env['stock.quant']
        StockLot = self.env['stock.lot']
        location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations')
        sequence = self.env['sequence.lot']

        created_lots = []
        lot_ids = self.env['sequence.lot'].search([])
        print('lot_ids----------------', lot_ids)
        for lot in lot_ids:
            print('lot----------', lot)
            for i in range(int(self.qty)):
                lots = StockLot.create({
                    'name': lot,
                    'product_id': self.pro_id.id,
                })
                print('lots--------', lots)
                # created_lots.append(lots.id)

                # Create stock.quant
                StockQuant.create({
                    'product_id': self.pro_id.id,
                    'location_id': location.id,
                    'quantity': 1.0,
                    'lot_id': lots.id,
                    'owner_id': self.crm_id.partner_id.id if self.crm_id else False,
                    'serial_no': self.serial_no,
                    'make_id': self.make_id.id,
                    'model_id': self.model_id.id,
                    'accesories': self.accesories,
                    'physical_status_id': self.physical_status_id.id,
                    'lead_id': self.lead_id.id

                })
                print('StockQuant-----------', StockQuant)

        # Assign lots to record
        self.lot_ids = [(6, 0, created_lots)]

        # Format serials
        serial_names = ', '.join([
            self.env['stock.lot'].browse(lot_id).name for lot_id in created_lots
        ])

        # Format display text
        formatted_text = f"Product: {self.pro_id.display_name}\n"
        formatted_text += f"Serials: ({serial_names})\n"

        if self.make_id:
            formatted_text += f"Make: {self.make_id.name}\n"
        if self.model_id:
            formatted_text += f"Model: {self.model_id.name}\n"
        # if self.accesories:
        #     formatted_text += f"Accessories: {self.accesories}\n"
        if self.physical_status_id:
            formatted_text += f"Physical Status: {self.physical_status_id.name}\n"

        # Save text to field
        self.lot_number_text = formatted_text
        self.is_quant_created = True

        # Open serials in a popup tree view
        view_id = self.env.ref('stock.view_stock_quant_tree_editable').id

        return {
            'name': _('Detailed Operations'),
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'views': [(view_id, 'tree')],
            'target': 'new',
            'domain': [('lot_id', 'in', created_lots)],
            'context': {
                'create': False,
                'default_location_id': location.id,
                'default_owner_id': self.crm_id.partner_id.id if self.crm_id else False,
                'show_lot_id': '1',

            }
        }

    #
    # def action_assign_serials(self):
    #     if self.is_quant_created:
    #         raise ValidationError(_("Already updated the qty"))
    #     if self.pro_id.tracking != 'serial':
    #         raise ValidationError(_("Please enable the configuration"))
    #
    #     self.ensure_one()
    #
    #     StockQuant = self.env['stock.quant']
    #     location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations')
    #
    #     created_lots = []
    #
    #     for i in range(int(self.qty)):
    #         StockQuant.create({
    #             'product_id': self.pro_id.id,
    #             'location_id': location.id,
    #             'quantity': 1.0,
    #             'owner_id': self.crm_id.partner_id.id if self.crm_id else False,
    #             'serial_no': self.serial_no,
    #             'make': self.make,
    #             'model': self.model,
    #             'accesories': self.accesories,
    #             'physical_status_id': self.physical_status_id.id,
    #         })
    #
    #     self.is_quant_created = True
    #
    #     # Open serials in a popup tree view
    #     view_id = self.env.ref('stock.view_stock_quant_tree_editable').id
    #
    #     return {
    #         'name': _('Detailed Operations'),
    #         'view_mode': 'tree',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'stock.quant',
    #         'views': [(view_id, 'tree')],
    #         'target': 'new',
    #         'domain': [('lot_id', 'in', created_lots)],
    #         'context': {
    #             'create': False,
    #             'default_location_id': location.id,
    #             'default_owner_id': self.crm_id.partner_id.id if self.crm_id else False,
    #             'show_lot_id': '1',
    #         }
    #     }

    @api.onchange('pro_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.pro_id:
                rec.des = rec.pro_id.name
                rec.unit_price = rec.pro_id.standard_price
            else:
                rec.des = ''
                rec.unit_price = ''

    def unlink(self):
        if self.is_quant_created:
            raise UserError(
                _("You cannot delete this service instrument because stock / delivery has already been created.")
            )
        return super(KGInspectionCalibration, self).unlink()

    def update_location(self):
        SequenceLot = self.env['sequence.lot']

        self.ensure_one()  # Ensure this method is only called for one record

        if not self.pro_id:
            raise UserError("Please select a Product.")
        if not self.pro_id.tracking == 'serial':
            raise UserError("Please select a Tracking as Unique serial Number.")
        if self.qty <= 0:
            raise UserError("Quantity must be greater than 0.")
        if not self.id:
            raise UserError("Please save the record before proceeding.")
        for product in self.pro_id:
            category = product.categ_id
            if not category:
                raise ValidationError(f"Product '{product.display_name}' has no category assigned.")
            if not any([
                category.is_calibration,
                category.is_lsa,
                category.is_ffa,
                category.is_navigation_communication,
                category.is_field_service
            ]):
                raise ValidationError(
                    f"Category of product '{product.display_name}' is not configured with Groups, Categories and certificates."
                )

        # Search for existing lots for this inspection
        existing_lots = SequenceLot.search([('inspection_calibration_id', '=', self.id)])

        if existing_lots:
            created_lots = existing_lots.ids
        else:
            created_lots = []
            for _ in range(int(self.qty)):
                lot = SequenceLot.create({
                    'pro_id': self.pro_id.id,
                    'inspection_calibration_id': self.id,
                    'lead_id': self.crm_id.id if self.crm_id else False,
                })
                created_lots.append(lot.id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Detailed Operations',
            'view_mode': 'tree',
            'res_model': 'sequence.lot',
            'domain': [('id', 'in', created_lots)],
            # 'target': 'new',
            'context': {
                'default_pro_id': self.pro_id.id,
                'create': False,
            }
        }

    def kg_views_product_location(self):
        self.ensure_one()

        return {
            'name': _('Detailed Operations'),
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
            'res_model': 'sequence.lot',
            'domain': [('inspection_calibration_id', '=', self.id)],
            'context': {
                'create': False,
                'default_pro_id': self.pro_id.id,
            }
        }


class ProductTemplate(models.Model):
    _inherit = "product.template"

    inspection_role_id = fields.Many2one('inspection.calibration', string="Inspection Request")
    lead_id = fields.Many2one('crm.lead', string="Inspection Request")


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    serial_no = fields.Char(string="Serial No")
    make = fields.Char(string="Make")
    make_id = fields.Many2one('rec.make', string='Make')
    model_id = fields.Many2one('rec.model', string='Model')
    model = fields.Char(string="Model")
    accesories = fields.Text(string="Accessories")
    physical_status_id = fields.Many2one('physical.status', string="Physical Status")
    remark = fields.Text(string='Remark', copy=False)
    lot_number_text = fields.Text(string='Serial Numbers')
    lead_id = fields.Many2one('crm.lead', string="Lead")
    inspection_calibration_id = fields.Many2one('inspection.calibration', string="Inspection")

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity=False, reserved_quantity=False, lot_id=None,
                                   package_id=None, owner_id=None, in_date=None, physical_status_id=None, make_id=None,
                                   model_id=None, accesories=None, lead_id=None, remark=None):
        """ Increase or decrease `quantity` or 'reserved quantity' of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.

        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        if not (quantity or reserved_quantity):
            raise ValidationError(_('Quantity or Reserved Quantity should be set.'))
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id,
                              strict=True)
        if lot_id and quantity > 0:
            quants = quants.filtered(lambda q: q.lot_id)

        if location_id.should_bypass_reservation():
            incoming_dates = []
        else:
            incoming_dates = [quant.in_date for quant in quants if quant.in_date and
                              float_compare(quant.quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = min(incoming_dates)
        else:
            in_date = fields.Datetime.now()

        quant = None
        if quants:
            self._cr.execute(
                "SELECT id FROM stock_quant WHERE id IN %s ORDER BY lot_id LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED",
                [tuple(quants.ids)])
            stock_quant_result = self._cr.fetchone()
            if stock_quant_result:
                quant = self.browse(stock_quant_result[0])
        print(lead_id, 'pppppppppppppppppppppppppppppp')

        if quant:
            vals = {'in_date': in_date}
            if quantity:
                vals['quantity'] = quant.quantity + quantity
            if reserved_quantity:
                vals['reserved_quantity'] = quant.reserved_quantity + reserved_quantity
            quant.write(vals)
            print(vals,"valsssssssssssssssss")

        else:
            vals = {
                'physical_status_id': physical_status_id.id if physical_status_id else False,
                'lead_id': lead_id.id if lead_id else False,
                'make_id': make_id.id if make_id else False,
                'model_id': model_id.id if model_id else False,
                'accesories': accesories,
                'remark': remark,
                'product_id': product_id.id,
                'location_id': location_id.id,
                'lot_id': lot_id and lot_id.id,
                'package_id': package_id and package_id.id,
                'owner_id': owner_id and owner_id.id,
                'in_date': in_date,
            }
            if quantity:
                vals['quantity'] = quantity
            if reserved_quantity:
                vals['reserved_quantity'] = reserved_quantity
            print(vals, 'vals')
            self.create(vals)
            print("llll")
        return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id,
                                            owner_id=owner_id, strict=True, allow_negative=True), in_date
