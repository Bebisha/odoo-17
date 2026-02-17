from odoo import models, fields


class JobCostingReportWizard(models.TransientModel):
    _name = 'job.costing.report.wizard'
    _description = 'Job Costing Report Wizard'

    sale_order_ids = fields.Many2many(
        'sale.order',
        string='Sale Orders',
        required=True
    )

    def action_print_job_costing(self):
        return self.env.ref(
            'kg_job_costing_analytic.action_job_costing_report_analytic'
        ).report_action(self.sale_order_ids)
