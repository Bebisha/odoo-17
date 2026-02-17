from odoo import models, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    sale_order_id = fields.Many2one(
        related='sale_line_id.order_id',
        store=True
    )

    def _get_analytic_distribution(self):
        self.ensure_one()

        # Priority 1: Sale Order Job
        if self.sale_line_id and self.sale_line_id.order_id.analytic_account_id:
            analytic = self.sale_line_id.order_id.analytic_account_id
            return {str(analytic.id): 100.0}

        # Fallback to default behavior
        return super()._get_analytic_distribution()

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _prepare_analytic_distribution(self):
        self.ensure_one()
        if self.move_id.sale_line_id.order_id.analytic_account_id:
            analytic = self.move_id.sale_line_id.order_id.analytic_account_id
            return {str(analytic.id): 100.0}
        return {}
