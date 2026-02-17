from datetime import date

from odoo import models, fields, api


class KGRfqWizard(models.Model):
    _name = "rfq.wizard"
    _description = "Create RFQ from SO"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    vendor_id = fields.Many2one('res.partner', string="Vendor")
    x_new_vendor_remark = fields.Char(string="Vendor Remark", copy=False)
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    estimation_id = fields.Many2one('crm.estimation', string='Estimation' )
    lead_id = fields.Many2one('crm.lead', string='Lead' )
    order_line_ids = fields.One2many('rfq.wizard.line', 'rfq_wiz_id', string='Order Lines')
    vessel_id = fields.Many2one('vessel.code', string='Vessel')
    is_rfq_created = fields.Boolean(string="RFQ Created", default=False, copy=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_ids = self._context.get('active_ids')
        if active_ids:
            sale = self.env['sale.order'].browse(active_ids[0])
            res['sale_id'] = sale.id
            res['estimation_id'] = sale.estimation_id.id
            res['lead_id'] = sale.estimation_id.lead_id.id if sale.estimation_id and sale.estimation_id.lead_id else False

            lines = []
            for line in sale.order_line:
                discount_product = sale._get_discount_product()
                if line.product_id != discount_product:
                    line_vals = (0, 0, {
                        'code': line.code,
                        'division_id': sale.division_id.id,
                        'product_id': line.product_id.id,
                        'units': line.product_uom.id,
                        'qty': line.product_uom_qty,
                        'product_code': line.product_id.default_code,
                        'name': line.name,
                        'price_unit': line.price_unit,
                        'sale_order_line_id': line.id,
                    })
                    lines.append(line_vals)
            res['order_line_ids'] = lines
        return res


    def kg_create_rfq_button(self):
        self.ensure_one()  # This method should only be used on a single wizard record
        orderline = []

        for line in self.order_line_ids:
            # Update Sale Order Line quantities
            if line.sale_order_line_id:
                so_line = line.sale_order_line_id

                # Compute and update balance_qty
                if so_line.balance_qty == 0.0:
                    so_line.balance_qty = so_line.product_uom_qty - line.qty
                else:
                    so_line.balance_qty -= line.qty

                # Ensure po_qty is updated based on actual ordered quantity
                so_line.po_qty = so_line.product_uom_qty - so_line.balance_qty

            # Prepare purchase order line values
            line_vals = (0, 0, {
                'code': line.code,
                'division_id': line.division_id.id,
                'product_id': line.product_id.id,
                'product_code': line.product_id.default_code,
                'name': line.name or line.product_id.name,
                'product_qty': line.qty,
                'price_unit': line.price_unit,
                'product_uom': line.units.id if line.units else line.product_id.uom_id.id,
                'taxes_id': False,
                'sale_id':self.sale_id.id
            })
            orderline.append(line_vals)
            vendor_code = self.vendor_id.vendor_code
            estimation = self.sale_id.opportunity_id.enq_no if self.sale_id.opportunity_id else self.sale_id.estimation_id.name
                # if self.sale_id.estimation_id
                # else self.sale_id.estimation_id.lead_id.enq_no
                # if self.sale_id and self.sale_id.estimation_id and self.sale_id.estimation_id.lead_id
                # else None

            print(estimation,"estimation")

            if estimation:
                print(estimation,"estimation")
                existing_rfqs = self.env['purchase.order'].search([
                    ('partner_id', '=', self.vendor_id.id),
                    ('name', 'ilike', f"{estimation}_{vendor_code}_")
                ])

                # Count existing and increment
                next_number = len(existing_rfqs) + 1
                next_number_str = str(next_number).zfill(2)  # 01, 02, etc.

                # Build the new RFQ name with incremental suffix
                name = f"{estimation}_{vendor_code}_{next_number_str}"

            else:
                # Search existing RFQs for this supplier and this enquiry
                existing_rfqs = self.env['purchase.order'].search([
                    ('partner_id', '=', self.vendor_id.id),
                    ('name', 'ilike', f"{vendor_code}_")
                ])

                # Determine next increment
                next_number = len(existing_rfqs) + 1
                next_number_str = str(next_number).zfill(2)  # 01, 02, etc.

                name = f"{vendor_code}_{next_number_str}"

            # vendor_code = self.vendor_id.vendor_code
            #
            # sequence = self.env['ir.sequence'].next_by_code('rfq.seq')
            # sequence_new = self.env['ir.sequence'].next_by_code('rfq.seq.new')
            #
            # estimation = (
            #     self.sale_id.estimation_id.lead_id.enq_no
            #     if self.sale_id.estimation_id
            #     else self.sale_id.estimation_id.lead_id.enq_no
            #     if self.sale_id and self.sale_id.estimation_id and self.sale_id.estimation_id.lead_id
            #     else None
            # )
            #
            # if estimation:
            #     name = f"{estimation}_{vendor_code}_{sequence}"
            # else:
            #     name = f"{vendor_code}_{sequence_new}"
        po_vals = {
            'name':name,
            'partner_id': self.vendor_id.id,
            'vessel_id': self.sale_id.vessel_id.id,
            'division_id': self.sale_id.division_id.id,
            'x_new_vendor_remark': self.x_new_vendor_remark,
            'order_line': orderline,
            'date_planned': date.today(),
            'so_ids': [(6, 0, self.sale_id.ids)],
            'currency_id': self.sale_id.currency_id.id if self.sale_id else self.env.company.currency_id.id,
        }

        # Create the Purchase Order
        po_id = self.env['purchase.order'].create(po_vals)

        # Link to Sale Order and other related fields
        if self.sale_id:
            self.sale_id.so_po_ids |= po_id
            po_id.vessel_id = self.sale_id.vessel_id.id
            po_id.estimation_id = self.sale_id.estimation_id.id
            po_id.opportunity_id = self.lead_id.id

        self.is_rfq_created = True


class KGRfqLineWizard(models.Model):
    _name = "rfq.wizard.line"
    _description = "Create RFQ Wizard Lines"

    rfq_wiz_id = fields.Many2one('rfq.wizard')
    product_id = fields.Many2one('product.product', string='Product')
    units = fields.Many2one('uom.uom', string='Units')
    qty = fields.Float(string="Quantity", default=1.00)
    product_code = fields.Char(string='Product Code')
    name = fields.Char(string='Description')
    price_unit = fields.Float(string="Unit Price")
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sale Line")
    total = fields.Float(string="Total", compute="compute_total_amount")
    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'),('ft','FT')
    ], string="Code")
    division_id = fields.Many2one("kg.divisions", string="Division")


    @api.depends('qty', 'price_unit')
    def compute_total_amount(self):
        for rec in self:
            if rec.qty or rec.price_unit:
                rec.total = rec.qty * rec.price_unit
            else:
                rec.total = 0.00

    @api.onchange('product_id')
    def get_description(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.standard_price
        else:
            self.name = False
