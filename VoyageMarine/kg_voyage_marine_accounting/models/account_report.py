from odoo import fields, models

class InheritAccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    type_id = fields.Selection([('local', 'Local'), ('meast', 'Middle east'), ('international', 'International'),
                                ('sisconcern', 'Sister Concern'), ('subcontracting', 'Subcontracting')],
                               default='sisconcern', string="Type", related='partner_id.po_type', store=True)

    division_id = fields.Many2one("kg.divisions", string="Division")

    def _select(self):
        return super()._select() + """,
               partner.po_type AS type_id,
               line.division_id AS division_id
           """
    #
    # def _group_by_sale(self):
    #     group_by_str = super()._group_by_sale()
    #     group_by_str += """,
    #         partner.po_type
    #     """
    #     return group_by_str

