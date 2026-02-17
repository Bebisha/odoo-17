from odoo.exceptions import ValidationError
from odoo import fields, models, api, _


class SaleQtnLines(models.Model):
    _name = 'sale.qtn.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Quotation Lines"

    qtn_so_id = fields.Many2one('sale.order')
    product_id = fields.Many2one("product.product", string="Product")
    description = fields.Text(string='Description', store=True)
    quantity = fields.Float(string='Qty', default=1)
    uom_id = fields.Many2one('uom.uom', string='UOM')
    unit_price = fields.Float(string='Unit Price')
    total = fields.Float(string='Total', compute='compute_total', store=True)
    name = fields.Char()
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('add_line_control', "Add a line")], default=False, help="Technical field for UX purpose.")
    tax_ids = fields.Many2many("account.tax", string="Taxes")
    boe_id = fields.Many2one("mrp.bom", string="BOE")

    @api.onchange('product_id')
    def onchange_product(self):
        for product in self:
            product.description = product.product_id.name
            product.uom_id = product.product_id.uom_id.id
            product.unit_price = product.product_id.standard_price
            bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', product.product_id.product_tmpl_id.id)],
                                                limit=1)
            if bom_id:
                product.boe_id = bom_id.id

    @api.depends('quantity', 'unit_price')
    def compute_total(self):
        for line in self:
            line.total = line.quantity * line.unit_price

    def unlink(self):
        for rec in self:
            if rec.boe_id:
                raise ValidationError(_("You can not delete a created BOE lines !!"))
            order_line_id = self.env['sale.order.line'].search([('qtn_line_ids', 'in', rec.id)])
            for line in order_line_id:
                line.unlink()
        return super(SaleQtnLines, self).unlink()

    def add_lines(self):
        for rec in self:
            for li in rec.qtn_so_id.order_line:
                if li.qtn_line_ids and rec.id in li.qtn_line_ids.ids:
                    li.qtn_line_ids = [(5, 0, 0)]
                    li.unlink()

            if rec.product_id:
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id)],
                                                    limit=1)
                if bom_id:
                    order_lines = []
                    for bom_line in bom_id.bom_line_ids:
                        line_vals = (0, 0, {
                            'product_id': bom_line.product_id.id,
                            'product_uom_qty': bom_line.product_qty,
                            'product_uom': bom_line.product_uom_id.id,
                            'qtn_line_ids': [(4, rec.id)]
                        })
                        order_lines.append(line_vals)

                    if rec.qtn_so_id:
                        rec.qtn_so_id.write({
                            'order_line': order_lines
                        })


class KGMRPLineInherit(models.Model):
    _inherit = "mrp.bom.line"

    sale_qtn_line_id = fields.Many2one("sale.qtn.line", string="QTN Line")
    sale_line_id = fields.Many2one("sale.order.line", string="SO Line")


class KGMRPIherit(models.Model):
    _inherit = "mrp.bom"

    sale_line_id = fields.Many2one("sale.order.line", string="SO Line")