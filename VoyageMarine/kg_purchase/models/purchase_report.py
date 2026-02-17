from odoo import fields, models


class PurchaseReports(models.Model):
    _inherit = "purchase.report"

    type_id = fields.Selection([('local', 'Local'), ('meast', 'Middle east'), ('international', 'International'),
                                ('sisconcern', 'Sister Concern'), ('subcontracting', 'Subcontracting')],
                               default='sisconcern', string="Type", related='partner_id.po_type', store=True)

    code = fields.Selection([
        ('ds', 'DS'), ('ms', 'MS'), ('os', 'OS'), ('rs', 'RS'), ('fl', 'FL'),
        ('fs', 'FS'), ('sl', 'SL'), ('ss', 'SS'), ('nl', 'NL'), ('ns', 'NS'),
        ('pl', 'PL'), ('ps', 'PS'), ('cl', 'CL'), ('cs', 'CS'), ('tr', 'TR'),
        ('ml', 'ML'), ('tl', 'TL'), ('rl', 'RL'), ('el', 'EL'), ('sm', 'SM'),
        ('fm', 'FM'), ('lm', 'LM'), ('nm', 'NM'), ('cm', 'CM'), ('rm', 'RM'),
        ('pm', 'PM'), ('om', 'OM'), ('mm', 'MM'), ('es', 'ES'), ('ft', 'FT')
    ], string="Code")

    product_code = fields.Char(string="Product Code", related='product_id.default_code', store=True)
    purchase_division_id = fields.Many2one('purchase.division', string='Purchase Division')
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        store=True
    )
    analytic_distribution = fields.Json(
        string="Analytic Distribution",
        readonly=True
    )
    analytic_account_name = fields.Char(
        string="Analytic Account",
        readonly=True
    )

    def _select(self):
        select_str = super()._select()
        select_str += """,
            partner.po_type AS type_id,
            product.default_code AS product_code,
            l.code AS code,
            po.purchase_division_id AS purchase_division_id,
        (jsonb_object_keys(l.analytic_distribution)::int) AS analytic_account_id
        """
        return select_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += """,
            partner.po_type,
            product.default_code,
            l.code,
            po.purchase_division_id,
        l.analytic_distribution
        """
        return group_by_str

    def _from(self):
        from_str = super()._from()
        from_str += """
            LEFT JOIN product_product product ON product.id = l.product_id
        """
        return from_str
