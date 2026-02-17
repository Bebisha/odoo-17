from odoo import fields, models, api


class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'

    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False,
                                 default=lambda self: self.env.company)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    material_request_line_id = fields.Many2one(
        'material.purchase.requisition',
        string='Material Request Item',
        ondelete='cascade', related='account_id.material_request_line_id', store=True
    )
    material_request_line_ids = fields.Many2many(
        'material.purchase.requisition',
        string='Material Request Item',
        ondelete='cascade', store=True, compute='_compute_material_request_line_ids',

    )

    @api.depends('account_id')
    def _compute_material_request_line_ids(self):
        for rec in self:
            rec.material_request_line_ids = rec.account_id.material_request_line_ids.ids


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    material_request_line_id = fields.Many2one(
        'material.purchase.requisition',
        string='Material Request Item',
        ondelete='cascade', store=True
    )
    material_request_line_ids = fields.Many2many(
        'material.purchase.requisition',
        string='Material Request Item',
        ondelete='cascade', store=True,
    )
