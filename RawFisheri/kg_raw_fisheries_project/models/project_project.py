from odoo import models, api, fields


class KGProjectInherit(models.Model):
    _inherit = "project.project"

    project_users_ids = fields.Many2many("res.users", string="Project Users")

    @api.model_create_multi
    def create(self, vals):
        res = super(KGProjectInherit, self).create(vals)
        if res.analytic_account_id:
            res.analytic_account_id.unlink()
        return res
