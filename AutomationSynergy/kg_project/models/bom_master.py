from odoo import models, fields, api


class BOMMaster(models.Model):
    _name = 'bom.master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _rec_name = 'product_id'

    name = fields.Char()
    show_bom_in = fields.Selection(selection=[('product', 'Product'), ('bom', 'BOM Category')], default='product')
    bom_category_id = fields.Many2one('bom.category', 'BOM Category')
    product_id = fields.Many2one('product.product', "Cabinet Product")
    category_ids = fields.Many2many('product.category')
    bom_line_ids = fields.One2many('bom.master.line', 'bom_id', ondelete='cascade')
    active = fields.Boolean(default=True)

    @api.model
    def create(self, values):
        if values['show_bom_in'] == 'product':
            product_name = self.env['product.product'].browse(values['product_id']).name
            values['name'] = product_name
        if values['show_bom_in'] == 'bom':
            category_name = self.env['bom.category'].browse(values['bom_category_id']).name
            values['name'] = category_name
        res = super(BOMMaster, self).create(values)
        return res

    @api.onchange('show_bom_in')
    def onchange_show_bom_in(self):
        if self.show_bom_in == 'bom':
            self.product_id = False

    @api.onchange('category_ids')
    def onchange_product_category_wise(self):
        self.bom_line_ids = [(5, 0, 0)]
        if self.category_ids:
            for category in self.category_ids:
                section_line = {
                    'display_type': 'line_section',
                    'name': category.name,
                }
                self.bom_line_ids = [(0, 0, section_line)]
                products = self.env['product.product'].search(
                    [('categ_id', '=', category._origin.id), ('detailed_type', '=', 'product')])

                for product in products:
                    product_line = {
                        'display_type': False,
                        'product_id': product.id,
                        'product_category_id': category.id,
                        'qty': 1,
                    }
                    self.bom_line_ids = [(0, 0, product_line)]


class BOMMasterLine(models.Model):
    _name = 'bom.master.line'

    bom_id = fields.Many2one('bom.master')
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    name = fields.Char('Category')
    product_id = fields.Many2one('product.product', 'Components')
    product_category_id = fields.Many2one('product.category', 'Product category')

    qty = fields.Float('Quantity', default=1)
    unit_price = fields.Float('Unit Price')
    subtotal = fields.Float('Sub Total', compute="compute_subtotal")
    uom_id = fields.Many2one('uom.uom')
    @api.onchange('product_id')
    def onchange_uom(self): 
        if self.product_id:
            self.uom_id = self.product_id.uom_po_id.id
    @api.depends('qty','unit_price')
    def compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.unit_price* rec.qty
