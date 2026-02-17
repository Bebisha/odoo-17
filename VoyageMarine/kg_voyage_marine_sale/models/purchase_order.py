from odoo import models, fields


class KGSalesPurchaseOrder(models.Model):
    _inherit = "purchase.order"
    _description = 'Request For Quotation'

    division_id = fields.Many2one("kg.divisions", string="Division")
    delivery_terms_id = fields.Many2one("delivery.terms",string="Delivery Terms" ,)

class KGPurchaseReports(models.Model):
    _inherit = "purchase.report"

    division_id = fields.Many2one("kg.divisions", string="Division", store=True, readonly=True)

    def _select(self):
        select_str = super()._select()
        select_str += """,
            po.division_id AS division_id
          """
        return select_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += """,
            po.division_id
          """
        return group_by_str



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    division_id = fields.Many2one("kg.divisions", string="Division",related='order_id.division_id',store=True)

    def _prepare_account_move_line(self, **optional_values):
        res = super()._prepare_account_move_line(**optional_values)
        print(res,"resresresres")

        # Only update the 'division_id' if a sale order exists
        if self.sale_id and not self.division_id:
            division = self.sale_id.division_id.id if self.sale_id.division_id else None
            res.update({
                'division_id': division
            })
            print(self.sale_id.division_id.id,"division_id")
            print(self.division_id,"division_id")
        res.update({
            'division_id': self.sale_id.division_id.id
        })

        return res
