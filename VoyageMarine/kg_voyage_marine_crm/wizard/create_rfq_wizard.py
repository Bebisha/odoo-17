from datetime import date

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class KGCreateRfqWizard(models.Model):
    _name = "kg.create.rfq.wizard"
    _description = "Create RFQ from SO"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    vendor_id = fields.Many2one('res.partner', string="Vendor")

    x_new_vendor_remark = fields.Char(string="Vendor Remark", copy=False)
    estimation_id = fields.Many2one('crm.estimation', string='Estimation')
    order_line_ids = fields.One2many('kg.create.rfq.wizard.line', 'rfq_wiz_id', string='Order Lines')
    opportunity_id = fields.Many2one("crm.lead", string="Opportunity")
    vessel_id = fields.Many2one('vessel.code', string='Vessel')
    is_rfq_created = fields.Boolean(string="RFQ Created", default=False, copy=False)


    def kg_create_rfq_button(self):
        orderline = []
        for line in self.order_line_ids:
            if self.estimation_id:
                for est in line.rfq_wiz_id.estimation_id:
                    order_line_id = est.material_cost_ids.filtered(lambda x: x.id == line.material_cost_id.id)
                    for vals in order_line_id:
                        if vals.balance_qty == 0.00:
                            vals.write({
                                'balance_qty': order_line_id.quantity - line.qty
                            })
                        else:
                            vals.update({
                                'balance_qty': order_line_id.balance_qty - line.qty
                            })
                        vals.po_qty = order_line_id.quantity - order_line_id.balance_qty

            line_vals = (0, 0, {
                'code': line.code,
                'product_id': line.product_id.id,
                'product_code': line.product_id.default_code,
                'name': line.name if line.name else line.product_id.name,
                'product_qty': line.qty,
                'price_unit': line.price_unit,
                'product_uom': line.units.id if line.units else line.product_id.uom_id.id,
                'taxes_id': False
            })
            orderline.append(line_vals)
        # vendor_code = self.vendor_id.vendor_code
        #
        # sequence = self.env['ir.sequence'].next_by_code('rfq.seq')
        # estimation = self.opportunity_id.enq_no if self.opportunity_id else self.estimation_id.lead_id.enq_no

        vendor_code = self.vendor_id.vendor_code
        if not vendor_code:
            raise ValidationError("Vendor code is missing on the supplier.")

        estimation = (self.opportunity_id.enq_no if self.opportunity_id else self.estimation_id.lead_id.enq_no)
        if not estimation:
            raise ValidationError("Enquiry Number is missing.")

        # Search existing RFQs for this vendor + enquiry
        existing_rfqs = self.env['purchase.order'].search([
            ('partner_id', '=', self.vendor_id.id),
            ('name', 'ilike', f"{estimation}_{vendor_code}_")
        ])

        # Compute next increment
        next_number = len(existing_rfqs) + 1
        next_number_str = str(next_number).zfill(2)

        # Build RFQ name
        rfq_name = f"{estimation}_{vendor_code}_{next_number_str}"

        vals = {
            'name':rfq_name,
            'partner_id': self.vendor_id.id,
            'x_new_vendor_remark': self.x_new_vendor_remark,
            'order_line': orderline,
            'date_planned': date.today(),
            'estimation_id':self.opportunity_id.estimation_id.id,
            'opportunity_id':self.opportunity_id.id,
            'currency_id': self.estimation_id.currency_id.id if self.estimation_id else self.env.company.currency_id.id
        }
        po_id = self.env['purchase.order'].create(vals)
        if self.estimation_id:
            self.estimation_id.po_ids |= po_id
            po_id.vessel_id = self.estimation_id.vessel_id.id
            po_id.estimation_id = self.estimation_id.id
        if self.opportunity_id:
            self.opportunity_id.po_ids |= po_id
            po_id.estimation_id = self.opportunity_id.estimation_id.id
            po_id.opportunity_id = self.opportunity_id.id
            po_id.vessel_id = self.opportunity_id.vessel_id.id


class KGCreateRfqLineWizard(models.Model):
    _name = "kg.create.rfq.wizard.line"
    _description = "Create RFQ Wizard Lines"

    rfq_wiz_id = fields.Many2one('kg.create.rfq.wizard')
    product_id = fields.Many2one('product.product', string='Product')
    units = fields.Many2one('uom.uom', string='Units')
    qty = fields.Float(string="Quantity", default=1.00)
    product_code = fields.Char(string='Product Code')
    name = fields.Char(string='Description')
    price_unit = fields.Float(string="Unit Price")
    material_cost_id = fields.Many2one('crm.material.cost', string="Material")
    item_id = fields.Many2one('crm.estimation.item', string="Item")
    total = fields.Float(string="Total", compute="compute_total_amount")
    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'),('ft','FT')
    ], string="Code")

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
