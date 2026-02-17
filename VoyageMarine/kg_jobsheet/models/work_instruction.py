from odoo import models, fields, api, _


class KgWorkInstruction(models.Model):
    _name = 'work.instruction'

    _rec_name = 'display_name'

    @api.depends('name', 'scope_id')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
            if rec.scope_id:
                rec.display_name = f"{rec.name} - {rec.scope_id.name}"

    display_name = fields.Char(compute='_compute_display_name')
    name = fields.Char(string="Work Instruction")

    scope_id = fields.Many2one('product.category', string="Scope")
    product_category_id = fields.Many2one('product.category', string="Equipment Category",
                                         )

    def load_job_costing_data(self):
        vals = []
        data = {
            'values': vals,
            'company_name': self.env.company.name,
            'company_zip': self.env.company.zip,
            'company_state': self.env.company.state_id.name,
            'company_country_code': self.env.company.country_id.code,
            'log_user_name':self.env.user.name
        }

        return self.env.ref('kg_jobsheet.kg_action_job_costing_report').with_context(
            landscape=False).report_action(self, data=data)
