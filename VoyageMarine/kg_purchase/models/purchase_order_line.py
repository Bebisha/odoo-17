from odoo import models, fields, api


class KGPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    sale_id = fields.Many2one('sale.order', string="Sale Order")
    image_1920 = fields.Image(string="Image", related='product_id.image_1920', readonly=True)
    product_code = fields.Char(string="Product Code",related='product_id.default_code', readonly=True)
    store_price_unit = fields.Float(string="Store Price Unit")
    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'),('ft','FT')
    ], string="Code")

    _sql_constraints = [
        ('accountable_required_fields',
         "CHECK(1=1)",
         "Missing required fields on accountable purchase order line."),
        ('non_accountable_null_fields',
         "CHECK(1=1)",
         "Forbidden values on non-accountable purchase order line"),
    ]

    @api.depends('product_id')
    def _compute_product_code(self):
        for line in self:
            line.product_code = line.product_id.default_code if line.product_id else ''

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id and rec.order_id:
                if not rec.product_uom:
                    rec.product_uom = rec.product_id.uom_po_id.id
                if rec.name:
                    rec.name = rec.name
                if rec.product_qty:
                    rec.product_qty = rec.product_qty
            return super(KGPurchaseOrderLine, self).onchange_product_id()

    def _prepare_account_move_line(self, **optional_values):
        res = super()._prepare_account_move_line(**optional_values)
        res.update({
            'code': self.code
        })

        return res
