from odoo import api, fields, models


class StockWarnInsufficientQtyLot(models.AbstractModel):
    _inherit = 'stock.warn.insufficient.qty'

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot / Serial Number',
        domain="[('product_id', '=', product_id)]"
    )

    @api.depends('product_id', 'lot_id')
    def _compute_quant_ids(self):
        for rec in self:
            company = rec._get_reference_document_company_id()

            domain = [
                *self.env['stock.quant']._check_company_domain(company),
                ('product_id', '=', rec.product_id.id),
                ('location_id.usage', '=', 'internal'),
            ]

            if rec.lot_id:
                domain.append(('lot_id', '=', rec.lot_id.id))

            rec.quant_ids = self.env['stock.quant'].search(domain)
