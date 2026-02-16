from ast import literal_eval

from odoo import models, fields, api, _
from datetime import datetime, date

from odoo.exceptions import ValidationError


class MaterialConsumption(models.Model):
    _name = "material.consumption"
    _description = "Material Consumption"
    _inherit = ['mail.thread']

    name = fields.Char(string="Reference No")
    date_from = fields.Datetime(string="Date From", default=datetime.now())
    date_to = fields.Datetime(string="Date To")
    material_consumption_ids = fields.One2many('material.consumption.line', 'material_consumption_id',
                                               string='Material Consumption Lines')
    company_id = fields.Many2one('res.company', readonly=True, default=lambda self: self.env.company)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('cancel', 'Cancel'), ('expire', 'Expired')], default='draft')
    destination_location = fields.Many2one('stock.location', string="Destination Location")
    move_ids = fields.Many2many('stock.move', string="Move Reference")
    sm_count = fields.Integer(string="SM Count", compute="compute_sm_count")
    is_expire = fields.Boolean(default=False)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('kg.,material.consumption.seq')
        return super(MaterialConsumption, self).create(vals)

    @api.onchange('date_from', 'date_to')
    def check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError(_("The start date must be less than the end date"))

    @api.depends('move_ids')
    def compute_sm_count(self):
        for rec in self:
            if rec.move_ids:
                rec.sm_count = len(rec.move_ids)
            else:
                rec.sm_count = 0

    def action_confirm(self):
        destination_location_id = self.env['ir.config_parameter'].sudo().get_param(
            'kg_mashirah_oil_manufacturing.destination_location', self.destination_location)

        if not destination_location_id:
            raise ValidationError(_('Please Select Destination Location in Configuration'))

        destination_location = self.env['stock.location'].search([('id', '=', int(destination_location_id))])

        for line in self.material_consumption_ids:
            vals = {
                'date': datetime.now(),
                'name': line.material_consumption_id.name,
                'reference': line.material_consumption_id.name,
                'product_id': line.product_id.id,
                'location_id': line.source_location.id,
                'location_dest_id': destination_location.id,
                'company_id': self.env.user.company_id.id,
                'quantity': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'create_uid': self.env.user.id,
                'state': 'done',
                # 'analytic_account_line_ids': [(4, line.cost_center.id)]
            }
            move_id = self.env['stock.move'].create(vals)
            self.move_ids = [(4, move_id.id)]
            self.env['account.analytic.line'].create({
                'account_id': line.cost_center.id,
                'product_id': line.product_id.id,
                'amount': line.product_id.standard_price * line.quantity,
                'name': line.product_id.name,
                'unit_amount': line.quantity,
                'company_id': self.env.user.company_id.id,
                'product_uom_id': line.product_id.uom_id.id,

            })
        self.write({
            'state': 'confirm'
        })

    def action_view_stock_moves(self):
        return {
            'name': 'Stock Moves',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'stock.move',
            'view_id': self.env.ref('stock.view_move_tree').id,
            'domain': [('id', 'in', self.move_ids.ids)],
            'target': 'current'
        }

    def update_state(self):
        material_id = self.search([('date_to', '<', date.today()), ('move_ids', '=', False), ('state', '=', 'confirm')])
        if material_id:
            for rec in material_id:
                rec.state = 'expire'
                rec.is_expire = True


class MaterialConsumptionLine(models.Model):
    _name = "material.consumption.line"
    _description = "Material Consumption Line"

    name = fields.Char(string="Name")
    material_consumption_id = fields.Many2one('material.consumption', string="Material Consumption")
    source_location = fields.Many2one("stock.location", string="Source Location")
    product_id = fields.Many2one("product.product", string="Equipment")
    lot_id = fields.Many2one("stock.lot", domain="[('product_id', '=', product_id)]", check_company=True, string="Lot")
    # cost_center = fields.One2many("account.analytic.line", 'material_consumption_line_id', string="Cost Center")
    cost_center = fields.Many2one("account.analytic.account", string="Cost Center")
    quantity = fields.Float(string="Quantity")
    company_id = fields.Many2one('res.company', readonly=True, default=lambda self: self.env.company)
    available_qty = fields.Float(string="Available Qty", related="product_id.qty_available")

    @api.onchange('quantity')
    def check_qty(self):
        for rec in self:
            if rec.available_qty and rec.quantity and rec.available_qty < rec.quantity:
                raise ValidationError("Quantity cannot be exceed the Available Quantity")
