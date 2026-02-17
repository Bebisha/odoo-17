from datetime import date
from odoo import models, fields, api


class EngagementPeriod(models.Model):
    _name = 'engagement.period'


    invoice_id = fields.Many2one('account.move',string="Invoice")
    project_contract_request_id = fields.Many2one('project.contract.request',string="Invoice")
    project_contract_amc_request_id = fields.Many2one('project.contract.request.amc',string="Invoice")
    invoice_ids = fields.One2many('account.move','engagement_period_id',string="Invoice")
    invoice_date = fields.Date(related='invoice_id.invoice_date', string="Invoice Date", store=True, readonly=True)
    invoice_state = fields.Selection(related='invoice_id.state', string="Invoice Status", store=True, readonly=True)
    payment_state = fields.Selection(related='invoice_id.payment_state', string="Payment Status", store=True, readonly=True)
    invoice_end_date = fields.Date( string="Invoice End Date",)
    period_start_date = fields.Date(string="Period Start Date")
    period_end_date = fields.Date(string="Period End Date")
    planned_hours = fields.Float(string='Planned Hours')
    rebion_pending = fields.Boolean(string="Pending Invoice")

    rebion_paid = fields.Boolean(
        string="Paid Invoice",
        compute="_compute_invoice_status_flags",
        store=True
    )

    @api.depends('invoice_end_date', 'payment_state')
    def _compute_invoice_status_flags(self):
        today = date.today()
        for record in self:
            record.rebion_pending = False
            record.rebion_paid = False

            if record.invoice_end_date and record.invoice_end_date <= today:
                if record.payment_state == 'paid':
                    record.rebion_paid = True
                else:
                    record.rebion_pending = True


