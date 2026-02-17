from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from io import BytesIO
import base64
from openpyxl import Workbook


class OnsiteContractDashboard(models.Model):
    _inherit = 'project.contract.request'


    sale_id = fields.Many2one('sale.order',string="Sale Order")
    recurrance_id = fields.Many2one(comodel_name='product.subscription.period', string='Recurrence Period')

    engagement_period_ids = fields.One2many('engagement.period','project_contract_request_id', string="Engagement Period")
    planned_hrs = fields.Float('Total Planned Hours')



    rebion_status = fields.Selection([
        ('pending', 'Draft'),
        ('done', 'Active'),
        ('completed', 'Completed'),
        ('expire', 'Expired'),

    ], string="Ribbon Status", compute="_compute_rebion_status", store=False, default="")

    # @api.depends('engagement_period_ids.invoice_date', 'engagement_period_ids.invoice_end_date',
    #              'engagement_period_ids.payment_state')
    # def _compute_rebion_status(self):
    #     today = date.today()
    #     for rec in self:
    #         rebion_pending = False
    #
    #         for period in rec.engagement_period_ids:
    #             if (
    #                     period.invoice_date and period.invoice_end_date and
    #                     period.invoice_date <= today <= period.invoice_end_date and
    #                     period.payment_state in ('not_paid', 'partial')
    #             ):
    #                 rebion_pending = True
    #                 break
    #
    #         rec.rebion_status = 'pending' if rebion_pending else 'done'
    #         if rec.state == 'complete':
    #             rec.rebion_status = 'completed'
    #         if rec.state == 'expire':
    #             rec.rebion_status = 'expire'
    @api.depends('date_start', 'date_end')
    def _compute_rebion_status(self):
        today = date.today()
        for rec in self:
            rec.rebion_status = 'pending'
            if rec.date_start and rec.date_end:
                if rec.date_start <= today <= rec.date_end:
                    rec.rebion_status = 'done'
                elif rec.date_end < today:
                    rec.rebion_status = 'expire'
                else:
                    rec.rebion_status = 'pending'


class AMCContractDashboard(models.Model):
    _inherit = 'project.contract.request.amc'

    sale_id = fields.Many2one('sale.order', string="Sale Order")
    contract_type = fields.Selection([('onsite', 'Onsite'), ('amc', 'AMC'), ('offshore', 'Offshore')],
                                    'Contract Type')
    engagement_period_ids = fields.One2many('engagement.period','project_contract_amc_request_id', string="Engagement Period")
    rebion_status = fields.Selection([
        ('pending', 'Inactive'),
        ('done', 'Active'),
        ('completed', 'Completed'),
        ('expire', 'Expired'),
    ], string="Ribbon Status", compute="_compute_rebion_status", store=False,default="")
    recurrance_id = fields.Many2one(comodel_name='product.subscription.period', string='Recurrence Period')
    planned_hrs = fields.Float('Total Planned Hours')
    support_hrs = fields.Float('Support Hours')
    enhancement_hrs = fields.Float('Enhancement Hours')
    spent_hrs = fields.Float('Total Hours Spent', compute='compute_spent_hrs')
    support_spent_hrs = fields.Float('Support Hours Spent', compute='compute_support_spent_hrs')
    enhancement_spent_hrs = fields.Float('Enhancement Hours Spent', compute='compute_enhancement_spent_hrs')
    spent_hrs_time = fields.Float('Hours Spent', compute='compute_spent_hrs_time')
    restrict_ticket = fields.Boolean("Restrict Ticket creation")
    task_count = fields.Integer(string='Task Count', compute='_compute_amc_counts')
    timesheet_count = fields.Integer(string='Timesheet Count', compute='_compute_amc_counts')
    description = fields.Char('Description')



    @api.depends('project_id', 'date_start', 'date_end')
    def _compute_amc_counts(self):
        for record in self:
            if record.project_id and record.date_start and record.date_end:
                task_domain = [
                    ('task_type', '!=', 'cr'),
                    ('project_id', '=', record.project_id.id),
                    ('date_start', '>=', record.date_start),
                    ('date_start', '<=', record.date_end),
                ]
                timesheet_domain = [
                    ('task_id.task_type', '!=', 'cr'),
                    ('project_id', '=', record.project_id.id),
                    ('date', '>=', record.date_start),
                    ('date', '<=', record.date_end),
                ]
                record.task_count = self.env['project.task'].search_count(task_domain)
                record.timesheet_count = self.env['account.analytic.line'].search_count(timesheet_domain)
            else:
                record.task_count = 0
                record.timesheet_count = 0

    # planned_hrs = fields.Float('Planned Hours')
    # spent_hrs = fields.Float('Hours Spent', compute='compute_spent_hrs')
    # spent_hrs_time = fields.Float('Hours Spent', compute='compute_spent_hrs_time')
    #
    # task_count = fields.Integer(string='Task Count', compute='_compute_amc_counts')
    # timesheet_count = fields.Integer(string='Timesheet Count', compute='_compute_amc_counts')

    @api.depends('project_id', 'date_start', 'date_end')
    def _compute_amc_counts(self):
        for record in self:
            if record.project_id and record.date_start and record.date_end:
                task_domain = [
                    ('task_type', '!=', 'cr'),
                    ('project_id', '=', record.project_id.id),
                    ('date_start', '>=', record.date_start),
                    ('date_start', '<=', record.date_end),
                ]
                timesheet_domain = [
                    ('task_id.task_type', '!=', 'cr'),
                    ('project_id', '=', record.project_id.id),
                    ('date', '>=', record.date_start),
                    ('date', '<=', record.date_end),
                ]
                record.task_count = self.env['project.task'].search_count(task_domain)
                record.timesheet_count = self.env['account.analytic.line'].search_count(timesheet_domain)
            else:
                record.task_count = 0
                record.timesheet_count = 0

    @api.depends('project_id', 'date_start', 'date_end')
    def compute_spent_hrs(self):
        for record in self:
            if record.project_id and record.date_start and record.date_end:
                tasks = self.env['project.task'].sudo().search([
                    ('project_id', '=', record.project_id.id),
                    ('date_start', '>=', record.date_start),
                    ('date_start', '<=', record.date_end),
                ])
                record.spent_hrs = sum(tasks.mapped('allocated_hours'))
            else:
                record.spent_hrs = 0.0

    @api.depends('project_id', 'date_start', 'date_end')
    def compute_support_spent_hrs(self):
        for record in self:
            if record.project_id and record.date_start and record.date_end:
                tasks = self.env['project.task'].sudo().search([
                    ('project_id', '=', record.project_id.id),
                    ('date_start', '>=', record.date_start),
                    ('date_start', '<=', record.date_end),
                    ('task_type','in',['bug']),
                ])
                record.support_spent_hrs = sum(tasks.mapped('allocated_hours'))
            else:
                record.support_spent_hrs = 0.0

    @api.depends('project_id', 'date_start', 'date_end')
    def compute_enhancement_spent_hrs(self):
        for record in self:
            if record.project_id and record.date_start and record.date_end:
                tasks = self.env['project.task'].sudo().search([
                    ('project_id', '=', record.project_id.id),
                    ('date_start', '>=', record.date_start),
                    ('date_start', '<=', record.date_end),
                    ('task_type', 'not in', ['bug']),
                ])

                record.enhancement_spent_hrs = sum(tasks.mapped('allocated_hours'))
            else:
                record.enhancement_spent_hrs = 0.0

    @api.depends('project_id', 'date_start', 'date_end')
    def compute_spent_hrs_time(self):
        for record in self:
            if record.project_id and record.date_start and record.date_end:
                tasks = self.env['account.analytic.line'].sudo().search([
                    ('project_id', '=', record.project_id.id),
                    ('date', '>=', record.date_start),
                    ('date', '<=', record.date_end),
                ])
                record.spent_hrs_time = sum(tasks.mapped('unit_amount'))
            else:
                record.spent_hrs_time = 0.0

    def view_tasks_amc(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "name": "Tasks",
            "res_model": 'project.task',
            "domain": [
                ('task_type', '!=', 'cr'),
                ('project_id', '=', self.project_id.id),
                ('date_start', '>=', self.date_start),
                ('date_start', '<=', self.date_end),
            ],
            "target": "current",
        }
        return action

    def view_timesheet_amc(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "name": "Timesheets",
            "res_model": 'account.analytic.line',
            "domain": [
                ('task_id.task_type', '!=', 'cr'),
                ('project_id', '=', self.project_id.id),
                ('date', '>=', self.date_start),
                ('date', '<=', self.date_end),
            ],
            "target": "current",
        }
        return action

    def cron_send_monthly_amc_spent_time(self):
        today = date.today()
        first_of_this_month = today.replace(day=1)
        last_month_start = first_of_this_month - relativedelta(months=1)
        last_month_end = first_of_this_month - timedelta(days=1)

        amc_contracts = self.search([
            ('date_start', '<=', last_month_end),
            ('date_end', '>=', last_month_start),
        ])

        rows = ""
        # Build summary table for internal team mail
        for contract in amc_contracts:
            timesheet_lines = self.env['account.analytic.line'].search([
                ('project_id', '=', contract.project_id.id),
                ('date', '>=', last_month_start),
                ('date', '<=', last_month_end),
            ])
            spent_hours = sum(timesheet_lines.mapped('unit_amount'))

            if contract.spent_hrs > 0:
                rows += f"""
                            <tr>
                                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{contract.po_no}</td>
                                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{contract.project_id.name or '-'}</td>
                                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{contract.partner_id.name or '-'}</td>
                                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{contract.spent_hrs:.2f} hrs</td>
                                <td style="border: 1px solid #ccc; padding: 8px; text-align: center;">{contract.planned_hrs:.2f} hrs</td>
                            </tr>
                        """

        #  Send summary mail to team
        if rows:
            period_str = f"{last_month_start.strftime('%d %b %Y')} - {last_month_end.strftime('%d %b %Y')}"
            subject = f"Monthly AMC Timesheet Summary – {last_month_start.strftime('%B %Y')}"
            body = f"""
                        <p>Dear Team,</p>
                        <p>Please find below the total hours spent on AMC contracts for the period <strong>{period_str}</strong>:</p>
                        <table style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">
                            <thead>
                                <tr style="background-color: #f2f2f2;">
                                    <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">Contract Name</th>
                                    <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">Project</th>
                                    <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">Customer</th>
                                    <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">Hours Spent</th>
                                    <th style="border: 1px solid #ccc; padding: 8px; text-align: center;">Planned Hours</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows}
                            </tbody>
                        </table>
                        <p>Regards,<br/>Odoo System</p>
                    """

            for user in amc_contracts.mapped('company_id.new_notification_users_ids'):
                if user.work_email:
                    mail = self.env['mail.mail'].create({
                        'subject': subject,
                        'body_html': body,
                        'email_to': user.work_email,
                    })
                    mail.send()

        # Partner specific emails with Excel attachment
        for contract in amc_contracts.filtered(lambda c: c.spent_hrs > 0 and c.partner_id.email):
            timesheet_lines = self.env['account.analytic.line'].search([
                ('project_id', '=', contract.project_id.id),
                ('date', '>=', last_month_start),
                ('date', '<=', last_month_end),
            ])
            spent_hours = sum(timesheet_lines.mapped('unit_amount'))
            planned_hours = contract.planned_hrs
            balance_hours = planned_hours - spent_hours

            partner_subject = f"AMC Contract Summary for {contract.po_no} – {last_month_start.strftime('%B %Y')}"
            partner_body = f"""
                    <p>Dear {contract.partner_id.name},</p>
                    <p>Please find below the total hours spent and planned for AMC Contract {contract.po_no} 
                       for the period <strong>{last_month_start.strftime('%d %b %Y')} - {last_month_end.strftime('%d %b %Y')}</strong>:</p>
                    <p><strong>Total Planned Hours:</strong> {planned_hours:.2f} hrs</p>
                    <p><strong>Total Spent Hours:</strong> {spent_hours:.2f} hrs</p>
                    <p><strong>Balance Hours:</strong> {balance_hours:.2f} hrs</p>
                    <p>We have also attached the detailed task-wise timesheet for your reference.</p>
                    <p>Regards,<br/>Odoo System</p>
                """

            #  Generate Excel with required columns
            wb = Workbook()
            ws = wb.active
            ws.title = "Tasks"
            ws.append(["Ticket No", "Task Name", "Hours Spent", "Task Status"])

            for line in timesheet_lines:
                ticket_no = ""
                if hasattr(line, "ticket_id") and line.ticket_id:
                    ticket_no = line.ticket_id.name
                elif line.task_id and hasattr(line.task_id, "ticket_id") and line.task_id.ticket_id:
                    ticket_no = line.task_id.ticket_id.name

                task_status = line.task_id.stage_id.name if line.task_id and line.task_id.stage_id else ""

                ws.append([
                    ticket_no,
                    line.task_id.name or "",
                    line.unit_amount,
                    task_status,
                ])

            fp = BytesIO()
            wb.save(fp)
            excel_data = base64.b64encode(fp.getvalue())
            fp.close()

            attachment = self.env['ir.attachment'].create({
                'name': f"{contract.po_no}_Timesheet_{last_month_start.strftime('%B_%Y')}.xlsx",
                'type': 'binary',
                'datas': excel_data,
                'res_model': 'mail.mail',
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })

            # Send partner mail with Excel
            mail = self.env['mail.mail'].create({
                'subject': partner_subject,
                'body_html': partner_body,
                'email_to': contract.partner_id.email,
                'attachment_ids': [(6, 0, [attachment.id])],
            })
            mail.send()

    @api.depends('date_start','date_end')
    def _compute_rebion_status(self):
        today = date.today()
        for rec in self:
            rec.rebion_status = 'pending'
            if rec.date_start and rec.date_end:
                if rec.date_start <= today <= rec.date_end:
                    rec.rebion_status = 'done'
                elif rec.date_end < today:
                    rec.rebion_status = 'expire'
                else:
                    rec.rebion_status = 'pending'



    # Commented on jul/17/25 as advised by sir
    # currently taking only contract start and end date
    # @api.depends('engagement_period_ids.invoice_date', 'engagement_period_ids.invoice_end_date',
    #              'engagement_period_ids.payment_state')
    # def _compute_rebion_status(self):
    #     today = date.today()
    #     for rec in self:
    #         today_paid = False
    #         today_unpaid = False
    #         unpaid_anywhere = False
    #         has_today_period = False
    #
    #         if not rec.engagement_period_ids:
    #             rec.rebion_status = 'pending'
    #         else:
    #             for period in rec.engagement_period_ids:
    #                 if period.payment_state in ('not_paid', 'partial'):
    #                     unpaid_anywhere = True
    #
    #                 if period.invoice_date and period.invoice_end_date:
    #                     if period.invoice_date <= today <= period.invoice_end_date:
    #                         has_today_period = True
    #                         if period.payment_state == 'paid':
    #                             today_paid = True
    #                             print("22222222")
    #                         else:
    #                             today_unpaid = True
    #
    #             if has_today_period:
    #                 if today_unpaid:
    #                     rec.rebion_status = 'pending'
    #                 else:
    #                     rec.rebion_status = 'done'
    #             else:
    #                 rec.rebion_status = 'pending'
    #
    #         # Final override for state
    #         if rec.state == 'complete':
    #             rec.rebion_status = 'completed'
    #         elif rec.state == 'expire':
    #             rec.rebion_status = 'expire'



