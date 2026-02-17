# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import date, timedelta

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
from ast import literal_eval
from dateutil.relativedelta import relativedelta


class KgSuccessPack(models.Model):
    _name = "kg.success.pack"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Kg Success Pack"
    _order = 'name desc'

    name = fields.Char(string='Name', required=True)
    hours = fields.Float(string='Hours', required=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    success_pack_line_ids = fields.One2many('kg.success.pack.line', 'success_pack_id', string='Success Pack Lines')
    product_id = fields.Many2one('product.product', readonly=True)
    amount = fields.Float(string="Amount")
    currency_id = fields.Many2one('res.currency', string="Currency")

    # def _send_weekly_report(self):
    #     today = date.today()
    #     start_date = today - timedelta(days=7)  # For context only
    #     formatted_start = start_date.strftime('%d-%m-%Y')
    #     formatted_today = today.strftime('%d-%m-%Y')
    #     pack_projects = self.env['pack.projects'].sudo().search([])
    #     projects = pack_projects.filtered(
    #         lambda x: x.start_date <= today and x.end_date >= start_date
    #     )
    #     project_partners = projects.mapped('partner_id')
    #
    #     for partner in project_partners:
    #         timesheets_all = self.env['account.analytic.line'].sudo().search([
    #             ('pack_project_id.partner_id', '=', partner.id)
    #         ])
    #
    #         packages = timesheets_all.mapped('task_id.success_pack_id')
    #
    #         def format_hours(hours_float):
    #             hours_int = int(hours_float)
    #             minutes = int(round((hours_float - hours_int) * 60))
    #             return f"{hours_int:02d}:{minutes:02d}"
    #
    #         summary_rows = ""
    #         for pack in packages:
    #             pack_timesheets_all = timesheets_all.filtered(lambda x: x.task_id.success_pack_id.id == pack.id)
    #             total_spent_hours = round(sum(pack_timesheets_all.mapped('unit_amount')), 2)
    #             remaining_hours = round(pack.hours - total_spent_hours, 2)
    #
    #             summary_rows += f"""
    #                 <tr>
    #                     <td>{pack.name}</td>
    #                     <td align="center">{format_hours(total_spent_hours)}</td>
    #                     <td align="center">{format_hours(remaining_hours)}</td>
    #                 </tr>
    #             """
    #
    #         if summary_rows:  # Only send if data exists
    #             subject = _("Weekly Success Pack Summary (%s to %s)", formatted_start, formatted_today)
    #             body = _(
    #                 """
    #                 <div style="font-family: Montserrat, sans-serif;font-size:12px;">
    #                     <p>Dear %s,</p>
    #                     <p>Please find below the summary of your success packs as of %s.</p>
    #                     <table border="1" cellpadding="5" cellspacing="0" style="font-size:12px; border-collapse: collapse;">
    #                         <thead>
    #                             <tr>
    #                                 <th>Success Pack</th>
    #                                 <th>Utilized Hours</th>
    #                                 <th>Remaining Hours</th>
    #                             </tr>
    #                         </thead>
    #                         <tbody>
    #                             %s
    #                         </tbody>
    #                     </table>
    #                     <p>We appreciate your continued partnership.</p>
    #                     <p>Please feel free to contact us if you have any questions.</p>
    #                     <p>Best Regards,<br/>
    #                     Success Pack Team,</p>
    #                     <p>Klystron Global</p>
    #                 </div>
    #                 """
    #             ) % (
    #                        partner.name,
    #                        formatted_today,
    #                        summary_rows
    #                    )
    #
    #             outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
    #             email_from = outgoing_mail_server.sudo().smtp_user if outgoing_mail_server else self.env.user.email
    #
    #             mail_values = {
    #                 'subject': subject,
    #                 'body_html': body,
    #                 'email_to': partner.email,
    #                 'email_from': email_from,
    #                 'email_cc': 'spp@klystronglobal.com',
    #                 'email_layout_xmlid': 'mail.mail_notification_layout_with_responsible_signature',  # Add this line
    #             }
    #
    #             print("mail_values", mail_values)
    #
    #             self.env['mail.mail'].sudo().create(mail_values).send()

    def _send_weekly_report(self):
        today = date.today()
        start_date = today - timedelta(days=7)
        formatted_start = start_date.strftime('%d-%m-%Y')
        formatted_today = today.strftime('%d-%m-%Y')

        pack_projects = self.env['pack.projects'].sudo().search([])

        projects = pack_projects.filtered(
            lambda x: (
                    x.start_date and x.end_date
                    and x.start_date <= today
                    and x.end_date >= start_date
            )
        )
        project_partners = projects.mapped('partner_id')

        template = self.env.ref('kg_success_pack.email_template_weekly_report')

        for partner in project_partners:
            tasks = self.env['project.task'].sudo().search([
                ('pack_project_id.partner_id', '=', partner.id)
            ])
            packages = tasks.mapped('success_pack_id')

            def format_hours(hours_float):
                hours_int = int(hours_float)
                minutes = int(round((hours_float - hours_int) * 60))
                return f"{hours_int:02d}:{minutes:02d}"

            summary_data = []
            for pack in packages:
                pack_tasks = tasks.filtered(lambda t: t.success_pack_id.id == pack.id)

                # use allocated_hours instead of timesheet unit_amount
                total_allocated_hours = round(sum(pack_tasks.mapped('allocated_hours')), 2)
                remaining_hours = round(pack.hours - total_allocated_hours, 2)

                summary_data.append({
                    'name': pack.name,
                    'utilized_hours': format_hours(total_allocated_hours),
                    'remaining_hours': format_hours(remaining_hours),
                })

            outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
            email_from = outgoing_mail_server.sudo().smtp_user if outgoing_mail_server else self.env.user.email

            if summary_data:
                template.with_context({
                    'start_date': formatted_start,
                    'end_date': formatted_today,
                    'summary_data': summary_data,
                }).send_mail(
                    partner.id,
                    force_send=True,
                    email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature',
                    email_values={
                        'email_from': email_from,
                        'email_to': partner.email,
                        'email_cc': 'spp@klystronglobal.com',
                    }
                )

    def _send_daily_report(self):
        records = self.env['kg.success.pack'].sudo().search([])
        # today = date.today()

        today = date.today() - timedelta(days=1)

        formatted_today = today.strftime('%d-%m-%Y')
        # lines = records.mapped('success_pack_line_ids').filtered(
        #     lambda x: x.active_pack and x.start_date <= today and x.end_date >= today)
        pack_projects = self.env['pack.projects'].sudo().search([])

        # projects = lines.mapped('pack_project_id')
        projects = pack_projects.filtered(
            lambda x: x.start_date <= today and x.end_date >= today)

        project_partners = projects.mapped('partner_id')

        for partner in project_partners:
            project = self.env['pack.projects'].sudo().search([('partner_id', '=', partner.id)])
            timesheets = self.env['account.analytic.line'].sudo().search([
                ('date', '=', today),
                ('pack_project_id.partner_id', '=', partner.id)
            ])
            print("timesheets", timesheets)
            timesheets_all = self.env['account.analytic.line'].sudo().search([
                ('pack_project_id.partner_id', '=', partner.id)
            ])

            packages = timesheets.mapped('task_id.success_pack_id')
            for pack in packages:
                pack_timesheets = timesheets.filtered(lambda x: x.task_id.success_pack_id.id == pack.id)
                pack_timesheets_all = timesheets_all.filtered(lambda x: x.task_id.success_pack_id.id == pack.id)
                total_spent_hours_today = round(sum(pack_timesheets.mapped('unit_amount')), 2)
                total_spent_hours = round(sum(pack_timesheets_all.mapped('unit_amount')), 2)
                remaining_hours = round(pack.hours - total_spent_hours, 2)

                vals = {
                    'date': today,
                    'success_package': pack.name,
                    'expected_hours': pack.hours,
                    'remaining_hours': remaining_hours,
                    'project': project[0].name,
                    'tasks': [{
                        'task': timesheet.task_id.name,
                        'description': timesheet.name,
                        'hours_spent': round(timesheet.unit_amount, 2),
                        'planned_hours': round(timesheet.task_id.allocated_hours, 2),
                    } for timesheet in pack_timesheets]
                }

                def format_hours(hours_float):
                    hours_int = int(hours_float)
                    minutes = int(round((hours_float - hours_int) * 60))
                    return f"{hours_int:02d}:{minutes:02d}"

                # Tasks for this report
                tasks = vals['tasks']

                # Build task rows
                task_rows = "".join(
                    "<tr>"
                    "<td>{task}</td>"
                    "<td>{description}</td>"
                    "<td align='center'>{hours_spent}</td>"
                    "</tr>".format(
                        task=task["task"],
                        description=task["description"],
                        hours_spent=format_hours(task["hours_spent"])
                    )
                    for task in tasks
                )

                # Add total hours row at bottom
                total_hours_row = """
                    <tr>
                        <td colspan="2" style="font-weight: bold; text-align: right;">Total Hours:</td>
                        <td align="center" style="font-weight: bold;">{}</td>
                    </tr>
                """.format(format_hours(total_spent_hours_today))

                task_rows += total_hours_row

                # Construct email subject and body
                subject = _("Success Package Daily Report for %s", today)
                body = _(
                    """
                    <div style="font-family: Montserrat, sans-serif;font-size:12px;">
                        <p>Dear %s,</p>
                        <p>Please find below the success pack utilization report based on the following subscription.</p>
                        <table style="border-collapse: collapse; margin-bottom: 1em;font-size:12px;">
                            <tr>
                                <td style="font-weight: bold; text-align: left; padding: 4px 12px 4px 0;">Report Date:</td>
                                <td style="padding: 4px 0;">%s</td>
                            </tr>
                            <tr>
                                <td style="font-weight: bold; text-align: left; padding: 4px 12px 4px 0;">Client:</td>
                                <td style="padding: 4px 0;">%s</td>
                            </tr>
                            <tr>
                                <td style="font-weight: bold; text-align: left; padding: 4px 12px 4px 0;">Success Pack:</td>
                                <td style="padding: 4px 0;">%s</td>
                            </tr>
                             <tr>
                                <td style="font-weight: bold; text-align: left; padding: 4px 12px 4px 0;">Total Hours Today:</td>
                                <td style="padding: 4px 0;">%s</td>
                            </tr>
                            <tr>
                                <td style="font-weight: bold; text-align: left; padding: 4px 12px 4px 0;">Total Hours Utilized:</td>
                                <td style="padding: 4px 0;">%s</td>
                            </tr> 

                            <tr>
                                <td style="font-weight: bold; text-align: left; padding: 4px 12px 4px 0;">Remaining Hours:</td>
                                <td style="padding: 4px 0;">%s</td>
                            </tr>
                        </table>
                        <table border="1" cellpadding="5" cellspacing="0" style="font-size:12px;">
                            <thead>
                                <tr>
                                    <th>Task</th>
                                    <th>Description</th>
                                    <th>Spent Hours</th>
                                </tr>
                            </thead>
                            <tbody>
                                %s
                            </tbody>
                        </table>
                        <p>We appreciate your continued partnership.</p>
                        <p>Please feel free to contact us if you have any questions.</p>
                        <p>Best Regards,<br/>
                        Success Pack Team,</p>
                        <p>Klystron Global</p>
                    </div>
                    """
                ) % (
                           partner.name,
                           formatted_today,
                           partner.name,
                           pack.name,
                           format_hours(total_spent_hours_today),
                           format_hours(total_spent_hours),
                           format_hours(remaining_hours),
                           task_rows
                       )

                # Here you'd add your email sending logic
                # e.g. self._send_email(partner.email, subject, body)

                # Now, you can pass the 'subject' and 'body' to your email sending function or service.

                outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
                email_from = outgoing_mail_server.sudo().smtp_user if outgoing_mail_server else self.env.user.email

                mail_values = {
                    'subject': subject,
                    'body_html': body,
                    'email_to': partner.email,
                    'email_from': email_from,
                    'email_cc': 'spp@klystronglobal.com',

                }
                print("mail_values", mail_values)

                self.env['mail.mail'].sudo().create(mail_values).send()

    @api.model_create_multi
    def create(self, vals_list):
        """Create a product corresponding to Success Pack"""
        product_obj = self.env['product.product']
        for vals in vals_list:
            product = product_obj.create({
                'name': vals.get('name', 'Unnamed'),
                'detailed_type': 'service',
                'is_success_pack': True,
                'list_price': vals.get('amount', 0.0),
            })

            vals['product_id'] = product.id
            product.product_tmpl_id.is_success_pack = True
        return super().create(vals_list)


class KgSuccessPackLine(models.Model):
    _name = "kg.success.pack.line"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default=lambda self: _('New'), copy=False, readonly=True)
    success_pack_id = fields.Many2one('kg.success.pack', 'Success Pack', required=True)
    pack_project_id = fields.Many2one('pack.projects', string='Pack Project', )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        default=lambda self: self.env.ref('kg_success_pack.success_pack_project_projects').id
    )
    partner_id = fields.Many2one('res.partner', string='Client', readonly=False)
    phone = fields.Char(related='partner_id.phone', string='Phone', readonly=False)
    email = fields.Char(related='partner_id.email', string='Email', readonly=False)
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date')
    estimated_hours = fields.Float(related="success_pack_id.hours", string='Planned Hours')
    worked_hours = fields.Float(string='Worked Hours', compute="compute_spent_hours")
    remaining_hours = fields.Float(string='Remaining Hours', compute="compute_spent_hours")
    utilization = fields.Selection([('normal', 'Normal'),
                                    ('over_utilized', 'Over Utilized'),
                                    ('not_utilized', 'Not Utilized')], string='Utilization')
    status = fields.Selection([('not_started', 'Draft'),
                               ('confirm', 'Confirm'),
                               ('contract', 'In Contract'),
                               ('closed', 'Closed')], string='Status', default="not_started", tracking=True)
    active_pack = fields.Boolean(string="Active", default=False)
    timesheet_ids = fields.Many2many('account.analytic.line', string='Timesheets')
    order_date = fields.Date(string='Order Date', copy=False, required=True)
    payment_date = fields.Date(string='Payment Date', copy=False)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    is_readonly = fields.Boolean()
    pm_id = fields.Many2one('hr.employee', string='Project Manager')
    sale_id = fields.Many2one('sale.order')

    def confirm_action(self):
        for rec in self:
            rec.status = 'confirm'

    def create_project_button(self):
        self.ensure_one()

        new_project = self.env['pack.projects'].create({
            'partner_id': self.partner_id.id,
            'name': f"{self.name} - {self.partner_id.name}",
            'start_date': self.start_date,
            'end_date': self.end_date,
            'estimated_hours': self.estimated_hours,
            'pm_id': self.pm_id.id if self.pm_id else False,
            'order_date': self.order_date,
            'success_pack_id': self.success_pack_id.id,
        })
        self.pack_project_id = new_project.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Project',
            'res_model': 'pack.projects',
            'view_mode': 'form',
            'res_id': new_project.id,
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        """ Create a sequence for the Success model """
        rec = super().create(vals_list)
        for vals in rec:
            if vals.name == _('New'):
                vals.name = (self.env['ir.sequence'].
                             next_by_code('success.pack.sequence'))
        rec.is_readonly = True

        return rec

    def toggle_active(self):
        for record in self:
            pack_lines = self.env['kg.success.pack.line'].sudo().search(
                [('partner_id', '=', self.partner_id.id), ('active_pack', '=', True), ('id', '!=', self.id)])
            if pack_lines:
                raise ValidationError(
                    _('You cannot activate multiple packages for the same project at the same time!!'))
            record.active_pack = not record.active_pack
            record.project_id.active_success_pack = record.active_pack
            record.start_date = fields.Date.today()
            record.end_date = record.start_date + relativedelta(years=1, days=-1)

    @api.onchange('start_date')
    def onchange_start_date(self):
        for record in self:
            if record.start_date:
                record.end_date = record.start_date + relativedelta(years=1, days=-1)

    def action_print_pdf(self):
        timesheets = self.env['account.analytic.line'].sudo().search([('date', '>=', self.start_date),
                                                                      ('date', '<=', self.end_date),
                                                                      ('partner_id', '=', self.partner_id.id),
                                                                      ('task_id.success_pack_id', '=',
                                                                       self.success_pack_id.id)])
        self.timesheet_ids = [(6, 0, timesheets.ids)]
        return self.env.ref('kg_success_pack.action_report_timesheets').report_action(self)

    def format_hours(self, decimal_hours):
        if decimal_hours is None:
            return "00:00"
        hours = int(decimal_hours)
        minutes = int(round((decimal_hours - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    def compute_status(self):
        for rec in self:
            today = date.today()
            # if rec.estimated_hours < rec.worked_hours:
            #     rec.utilization = 'over_utilized'
            # elif rec.worked_hours == 0:
            #     rec.utilization = 'not_utilized'
            # else:
            #     rec.utilization = 'normal'
            if rec.start_date and rec.end_date:
                if rec.start_date <= today <= rec.end_date:
                    rec.status = 'contract'
                elif rec.start_date > today:
                    rec.status = 'not_started'
                else:
                    rec.status = 'closed'
            else:
                rec.status = 'not_started'

    @api.onchange('start_date', 'end_date')
    def onchange_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(_('Start Date must be less than End Date'))

    @api.depends('start_date', 'end_date', 'pack_project_id')
    @api.onchange('start_date', 'end_date', 'pack_project_id')
    def compute_spent_hours(self):
        for rec in self:
            timesheets = self.env['account.analytic.line'].sudo().search([('date', '>=', rec.start_date),
                                                                          ('date', '<=', rec.end_date),
                                                                          ('partner_id', '=', rec.partner_id.id),
                                                                          ('task_id.success_pack_id', '=',
                                                                           rec.success_pack_id.id)])
            rec.worked_hours = sum(timesheets.mapped('unit_amount'))
            rec.remaining_hours = rec.estimated_hours - rec.worked_hours
            print("remaining_hours",rec.remaining_hours)

    def action_view_hours(self):
        timesheets = self.env['account.analytic.line'].sudo().search([('date', '>=', self.start_date),
                                                                      ('date', '<=', self.end_date),
                                                                      ('partner_id', '=', self.partner_id.id),
                                                                      ('task_id.success_pack_id', '=',
                                                                       self.success_pack_id.id)])
        all_dates = timesheets.mapped('date')
        created_timesheets = []
        for dt in list(set(all_dates)):
            dt_timesheets = timesheets.filtered(lambda x: x.date == dt)
            vals = {
                'success_pack_line_id': self.id,
                'timesheet_ids': [(6, 0, dt_timesheets.ids)],
                'date': dt,
                'hours_spent': sum(dt_timesheets.mapped('unit_amount'))

            }
            timesheets_val = self.env['pack.timesheet'].create(vals)
            created_timesheets.append(timesheets_val.id)
        return created_timesheets

    def action_view_timesheet(self):
        self.env['pack.timesheet'].search([]).unlink()
        timesheets = self.env['account.analytic.line'].sudo().search([('date', '>=', self.start_date),
                                                                      ('date', '<=', self.end_date),
                                                                      ('partner_id', '=', self.partner_id.id),
                                                                      ('task_id.success_pack_id', '=',
                                                                       self.success_pack_id.id)])
        all_dates = timesheets.sudo().mapped('date')
        for dt in list(set(all_dates)):
            dt_timesheets = timesheets.sudo().filtered(lambda x: x.date == dt)
            vals = {
                'success_pack_line_id': self.id,
                'timesheet_ids': [(6, 0, dt_timesheets.sudo().ids)],
                'date': dt,
                'hours_spent': sum(dt_timesheets.mapped('unit_amount'))

            }
            self.env['pack.timesheet'].create(vals)
        action = {
            "type": "ir.actions.act_window",
            "res_model": "pack.timesheet",
            "name": _("Timesheets"),
            "context": {"create": False},
            "view_mode": "tree",
            "views": [(False, 'tree')],
            "target": "new",
            "domain": [('pack_project_id', '=', self.id)],
        }
        return action

    def get_success_pack_line_data(self):
        success_pack_lines = self.env['sale.order'].search([('pack_project_id', '!=', False)])
        data = []
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        domain = []
        teams = self.env['project.team'].sudo().search([('timesheet_user_ids', '=', user.id)])
        project_obj = self.env['pack.projects'].sudo().search([])
        print("project_obj", project_obj)
        packages = [{"id": pack.id, "name": pack.name} for pack in self.env['kg.success.pack'].sudo().search([])]
        projects = [{"id": project.id, "name": project.name} for project in project_obj]
        customers = [{"id": customer.id, "name": customer.name} for customer in project_obj.sudo().mapped('partner_id')]
        companies = self.env.user.company_ids
        company_data = [{"id": company.id, "name": company.name} for company in companies]
        status = [
            val for key, val in self.env['pack.projects']
            .fields_get(allfields=['stages'])['stages']['selection']
        ]
        # status = [val for key, val in success_pack_lines.pack_project_id['stages'].selection]

        print("status", status)
        if not is_admin:
            user_ids = teams.mapped('employee_ids').sorted('name')
            domain.append(('user_id', 'in', user_ids.ids))
        elif not is_admin:
            domain.append(('user_ids', '=', user.id))

        for line in success_pack_lines:
            print("fgdgfdg",self.format_hours(line.worked_hours))
            # state = dict(line._fields['status'].selection).get(line.status, '') if line else ''
            # utilization = dict(line._fields['utilization'].selection).get(line.utilization, '') if line else ''
            data.append({
                'name': line.success_pack_id.name,
                'id': line.id,
                'project_name': line.pack_project_id.name,
                'project_id': line.pack_project_id.id,
                'pack_id': line.success_pack_id.id,
                'customer_name': line.pack_project_id.partner_id.name,
                'partner_id': line.pack_project_id.partner_id.id,
                'start_date': line.pack_project_id.start_date.strftime('%d/%m/%Y') if line.start_date else '',
                'end_date': line.pack_project_id.end_date.strftime('%d/%m/%Y') if line.end_date else '',
                'estimated_hours': self.format_hours(line.estimated_hours),
                'worked_hours': self.format_hours(line.worked_hours),
                # 'utilization': utilization,
                'status': dict(line.pack_project_id._fields['stages'].selection).get(line.pack_project_id.stages),
                'company_id': line.success_pack_id.company_id.id,
            })
        return {'vals': data, 'is_admin': is_admin, 'company_data': company_data, 'projects': projects,
                'packages': packages, 'customers': customers, 'status': status, }


class ProductProduct(models.Model):
    _inherit = "product.product"

    is_success_pack = fields.Boolean(default=False, string="Is Success Pack Product")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_success_pack = fields.Boolean(default=False, string="Is Success Pack Product")
