from odoo import models, api, fields


class KGAccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    parent_id = fields.Many2one("account.analytic.account", string="Parent Account")

    @api.model_create_multi
    def create(self, vals_list):
        analytic_lines = super(KGAccountAnalyticLine, self).create(vals_list)
        for line in analytic_lines:
            for field_name in line._fields:
                if field_name.startswith("x_plan") and field_name.endswith("_id"):
                    field_value = getattr(line, field_name)
                    if field_value:
                        line.parent_id = field_value.parent_id.id
        return analytic_lines
