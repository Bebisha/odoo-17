from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class KGSequence(models.Model):
    _name = "sequence.lot"
    _description = "Lot Sequence"

    _sql_constraints = [
        ('unique_sequence_name', 'unique(name)', 'The sequence number must be unique!')
    ]

    name = fields.Char(string="Sequence Number")
    pro_id = fields.Many2one('product.product', string="Product", domain="[('detailed_type','=','product')]")
    product_temp_id = fields.Many2one('product.template', string="Product Template")
    make = fields.Char(string="Make", )
    make_id = fields.Many2one('rec.make', string='Make')
    model_id = fields.Many2one('rec.model', string='Model')
    serial_no = fields.Char(string="Serial number", compute="_compute_sale_sequence")
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
    remark = fields.Text(string='Remark', copy=False)
    lot_number_text = fields.Text(string='Serial Numbers')
    lot_ids = fields.Many2many('stock.lot', string='Assigned Serials')
    inspection_calibration_id = fields.Many2one('inspection.calibration', string="Inspection")
    lead_id = fields.Many2one('crm.lead', string="Lead")
    is_created = fields.Boolean()

    @api.depends('serial_no')
    def _compute_sale_sequence(self):
        number = 1
        for record in self:
            record.serial_no = str(number)
            number += 1

    @api.onchange('pro_id')
    def _onchange_order_line_set_sn(self):
        sl_no = 1
        for line in self.pro_id:
            # if line.display_type not in ('line_note', 'line_section') and line.is_product_select:
            line.serial_no = sl_no
            sl_no += 1

    def action_create_stock_quant(self):
        if not self.name:
            raise ValidationError(_("Please enter the Serial No/ID No"))

        if self.is_created:
            raise ValidationError(_("Already updated the qty"))

        if self.pro_id.tracking != 'serial':
            raise ValidationError(_("Please enable the unique Serial Number"))

        StockQuant = self.env['stock.quant']
        StockLot = self.env['stock.lot']
        location = self.env.ref('kg_jobsheet.kg_jobsheet_used_locations')

        created_lot_ids = []

        for record in self:
            if not record.name:
                raise UserError(_("The 'Serial No/ID No' field must not be empty."))
            if not record.pro_id:
                raise UserError(_("Please select a Product."))
            if record.qty <= 0:
                raise UserError(_("Quantity must be greater than 0."))

            # Search or create the lot
            lot = StockLot.search([
                ('name', '=', record.name),
                ('product_id', '=', record.pro_id.id)
            ], limit=1)

            if not lot:
                lot = StockLot.create({
                    'name': record.name,
                    'product_id': record.pro_id.id,
                })

            # Create stock quant for the serial-tracked product
            StockQuant.create({
                'product_id': record.pro_id.id,
                'location_id': location.id,
                'quantity': 1.0,
                'lot_id': lot.id,
                'make_id': record.make_id.id,
                'model_id': record.model_id.id,
                'accesories': record.accesories,
                'remark': record.remark,
                'lot_number_text': record.lot_number_text,
                'physical_status_id': record.physical_status_id.id,
                'lead_id': record.lead_id.id,
                'inspection_calibration_id': record.inspection_calibration_id.id

            })

            created_lot_ids.append(lot.id)
            record.is_created = True
            record.lot_ids = [(6, 0, created_lot_ids)]

            # Prepare the lot detail text
            # Prepare the lot detail text with Model before Serial No
            lot_info_parts = []
            if record.make_id:
                lot_info_parts.append(f"Make: {record.make_id.name}")

            if record.model_id:
                lot_info_parts.append(f"Model: {record.model_id.name}")
            lot_info_parts.append(f"Serial No: {lot.name}")
            if record.physical_status_id:
                lot_info_parts.append(f"Status: {record.physical_status_id.name}")
            if record.accesories:
                lot_info_parts.append(f"Accessories: {record.accesories}")

            # Join parts to form the lot_info string
            lot_info = ", ".join(lot_info_parts)

            # Append or assign to lot_number_text
            record.lot_number_text = (record.lot_number_text + "\n" + lot_info) if record.lot_number_text else lot_info

            # Handle calibration update if applicable
            calibration = record.inspection_calibration_id
            if calibration:
                all_related = self.search([('inspection_calibration_id', '=', calibration.id)])
                if all(line.is_created for line in all_related):
                    calibration.is_quant_created = True
                    calibration.lot_number_text = "\n".join(
                        filter(None, (line.lot_number_text for line in all_related)))

                    # calibration.lot_number_text = formatted_text

        # view_id = self.env.ref('stock.view_stock_quant_tree_editable').id
        #
        # return {
        #     'name': _('Detailed Operations'),
        #     'view_mode': 'tree',
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'stock.quant',
        #     'views': [(view_id, 'tree')],
        #     'target': 'new',
        #     'domain': [('lot_id', 'in', created_lot_ids)],
        #     'context': {
        #         'create': False,
        #         'default_location_id': location.id,
        #         'show_lot_id': True,
        #     }
        # }
