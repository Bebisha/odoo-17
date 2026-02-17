# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import date

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
from ast import literal_eval
from dateutil.relativedelta import relativedelta


class PackProjects(models.Model):
    _name = "pack.projects"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Name", placeholder="Project Name",  required=True)
    sale_id = fields.Many2one('sale.order', string="Sale")
    partner_id = fields.Many2one('res.partner', string="Client", required=True)
    success_pack_line_ids = fields.One2many('kg.success.pack.line', 'pack_project_id', string='Success Pack Lines')
    timesheet_ids = fields.Many2many('account.analytic.line', string='Timesheets')
    task_ids = fields.Many2many('project.task', string='Tasks', copy=False, compute="_compute_linked_task")
    task_count = fields.Float(string='Tasks Count', copy=False, compute="_compute_task_count")
    success_pack_count = fields.Float(string='Success Pack Count', copy=False, compute="_compute_success_pack_count")
    stages = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('hold', 'Hold'),
        ('closed', 'Closed'),
    ],
        string='Status',
        tracking=True,
        default='draft',
    )
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date',tracking=True, readonly=True)
    order_date = fields.Date(string='Order Date', copy=False, required=True)
    success_pack_id = fields.Many2one('kg.success.pack', 'Success Pack')
    pm_id = fields.Many2one('hr.employee', string='Project Manager')

    estimated_hours = fields.Float(related="success_pack_id.hours", string='Planned Hours')
    worked_hours = fields.Float(string='Worked Hours', compute="compute_spent_hours")
    remaining_hours = fields.Float(string='Remaining Hours', compute="compute_spent_hours")
    email = fields.Char(related='partner_id.email', store=True, readonly=True,string='Email')
    phone = fields.Char(related='partner_id.phone', store=True, readonly=True,string="Phone")
    lead_id = fields.Many2one('hr.employee', string="Team Lead")
    worked_hours_kanban = fields.Char(
        string="Worked Hours (Kanban)",
        compute="_compute_spent_hours"
    )
    remaining_hours_kanban = fields.Char(
        string="Remaining Hours (Kanban)",
        compute="_compute_spent_hours"
    )


    @api.constrains('start_date',)
    def validation_error(self):
        for rec in self:
            if rec.order_date and rec.start_date:
                if rec.start_date < rec.order_date:
                    raise ValidationError("Start date cannot be earlier order date")

    @api.depends('start_date', 'end_date','task_ids')
    @api.onchange('start_date', 'end_date','task_ids')
    def compute_spent_hours(self):
        def format_hours(hours_float):
            hours_int = int(hours_float)
            minutes = int(round((hours_float - hours_int) * 60))
            return f"{hours_int:02d}:{minutes:02d}"
        for rec in self:
            # timesheets = self.env['account.analytic.line'].sudo().search([('date', '>=', rec.start_date),
            #                                                               ('date', '<=', rec.end_date),
            #                                                               ('pack_project_id', '=', rec.id),
            #                                                               ('partner_id', '=', rec.partner_id.id),
            #                                                               ('task_id.success_pack_id', '=',
            #                                                                rec.success_pack_id.id)])
            task_ids = self.env['project.task'].search([('pack_project_id', '=',  rec.id)])
            rec.worked_hours = sum(task_ids.mapped('allocated_hours'))
            rec.remaining_hours = rec.estimated_hours - rec.worked_hours
            rec.worked_hours_kanban = self._float_to_time(rec.worked_hours)
            rec.remaining_hours_kanban = self._float_to_time(rec.remaining_hours)
            print("remaining_hours_kanban",rec.remaining_hours_kanban)

    def _float_to_time(self, value):
        if value is None:
            return "00:00"
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"


    def action_view_timesheet(self):
        self.env['pack.timesheet'].sudo().search([]).unlink()
        timesheets = self.env['account.analytic.line'].sudo().search([('date', '>=', self.start_date),
                                                                   ('date', '<=', self.end_date),
                                                                   ('partner_id', '=', self.partner_id.id),
                                                                   ('pack_project_id', '=', self.id),
                                                                    ('task_id.success_pack_id', '=',self.success_pack_id.id)])

        all_dates = timesheets.sudo().mapped('date')
        for dt in list(set(all_dates)):
            dt_timesheets = timesheets.sudo().filtered(lambda x:x.date == dt)
            vals = {
                'pack_project_id': self.id,
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

    def action_view_hours(self):
        timesheets = self.env['account.analytic.line'].sudo().search([('date', '>=', self.start_date),
                                                               ('date', '<=', self.end_date),
                                                               ('partner_id', '=', self.partner_id.id),
                                                               ('task_id.success_pack_id', '=',self.success_pack_id.id)])
        all_dates = timesheets.mapped('date')
        created_timesheets=[]
        for dt in list(set(all_dates)):
            dt_timesheets = timesheets.filtered(lambda x: x.date == dt)
            vals = {
                'pack_project_id': self.id,
                'timesheet_ids': [(6, 0, dt_timesheets.ids)],
                'date': dt,
                'hours_spent': sum(dt_timesheets.mapped('unit_amount'))

            }
            timesheets_val = self.env['pack.timesheet'].create(vals)
            created_timesheets.append(timesheets_val.id)
        return created_timesheets

    def action_print_pdf(self):
        timesheets = self.env['account.analytic.line'].sudo().search([('date', '>=', self.start_date),
                                                                      ('date', '<=', self.end_date),
                                                                      ('partner_id', '=', self.partner_id.id),
                                                                      ('task_id.success_pack_id', '=',
                                                                       self.success_pack_id.id)])
        self.timesheet_ids = [(6, 0, timesheets.ids)]
        return self.env.ref('kg_success_pack.action_report_timesheets').report_action(self)

    @api.onchange('start_date')
    def onchange_start_date(self):
        for rec in self:
            if rec.start_date:
                rec.end_date = rec.start_date + relativedelta(years=1,days=-1)


    def hold_button(self):
        for rec in self:
            rec.stages = 'hold'

    def action_start_project(self):
        for rec in self:
            if not rec.start_date:
                raise ValidationError('Please add Start Date for this project')
            rec.stages = 'in_progress'

    def closed_button(self):
        for rec in self:
            if rec.remaining_hours > 0:
                raise ValidationError("You cannot close this as the estimated hours is not completed")
            else:
                rec.stages = 'closed'
                if rec.partner_id and rec.partner_id.email:
                    mail_values = {
                        'subject':  f"""Your Success pack for {rec.estimated_hours} is  Closed""",
                        'body_html': f"""
                                        <p>Dear {rec.partner_id.name},</p>
                                        <p>We are pleased to inform you that your Success pack for {rec.estimated_hours} Hrs <strong>{rec.name}</strong> has been closed.</p>
                                        <p>Thank you for working with us!</p>
                                        <p>Best regards,<br/>{self.env.user.name}</p>
                                    """,
                        'email_from': self.env.user.email or 'noreply@example.com',
                        'email_to': rec.partner_id.email,
                    }
                    self.env['mail.mail'].create(mail_values).send()
    def cron_close_button(self):
        """Button for closing projects automaticaly"""
        today = fields.Date.context_today(self)
        projects = self.env['pack.projects'].search([
            ('end_date', '<', today)
        ])
        for rec in projects:
            if rec.stages != 'closed':
                if rec.remaining_hours > 0:
                    raise ValidationError("You cannot close this as the estimated hours is not completed")
                else:
                    rec.stages = 'closed'
                    if rec.partner_id and rec.partner_id.email:
                        mail_values = {
                            'subject':  f"""Your Success pack for {rec.estimated_hours} is  Closed""",
                            'body_html': f"""
                                            <p>Dear {rec.partner_id.name},</p>
                                            <p>We are pleased to inform you that your Success pack for {rec.estimated_hours} Hrs <strong>{rec.name}</strong> has been closed.</p>
                                            <p>Thank you for working with us!</p>
                                            <p>Best regards,<br/>{self.env.user.name}</p>
                                        """,
                            'email_from': self.env.user.email or 'noreply@example.com',
                            'email_to': rec.partner_id.email,
                        }
                        self.env['mail.mail'].create(mail_values).send()




    def action_create_task(self):
        if not self.start_date:
            raise ValidationError("Please enter start date of the project before creating task")
        """ To create task from pack """
        project = self.env.ref('kg_success_pack.success_pack_project_projects')
        form_view = self.env.ref('kg_success_pack.success_pack_task_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'view_mode': 'form',
            'res_model': 'project.task',
            'context': {'default_pack_project_id': self.id, 'default_project_id': project.id},
            'view_id': form_view.id,
        }

    def _compute_linked_task(self):
        """Compute the tasks which are linked in the packs"""
        for record in self:
            tasks = self.env['project.task'].search([('pack_project_id', '=', record.id)])
            record.task_ids = [fields.Command.link(task.id) for task in tasks]

    @api.depends('task_ids')
    def _compute_task_count(self):
        """Compute the total count of tasks"""
        for pack in self:
            pack.task_count = len(pack.task_ids)

    @api.depends('success_pack_line_ids')
    def _compute_success_pack_count(self):
        """ compute the total count of success pack """
        for pack in self:
            pack.success_pack_count = len(pack.success_pack_line_ids)

    def action_get_tasks(self):
        """ Button action to show the tasks which are linked in the pack """
        self.ensure_one()
        tree_view = self.env.ref('kg_success_pack.success_pack_task_tree')
        form_view = self.env.ref('kg_success_pack.success_pack_task_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Task',
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'context': {'create': False},
            'domain': [('id', 'in', self.task_ids.ids)]
        }

    def action_get_packs(self):
        """ Kanban view: To view pack  """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Success pack',
            'view_mode': 'form',
            'res_model': 'pack.projects',
            'res_id': self.id,
            'context': {'create': False},
        }
    def format_hours(self, decimal_hours):
        if decimal_hours is None:
            return "00:00"
        hours = int(decimal_hours)
        minutes = int(round((decimal_hours - hours) * 60))
        return f"{hours:02d}:{minutes:02d}"

    def get_success_pack_line_data(self):
        success_pack_lines = self.env['sale.order'].sudo().search([('pack_project_id','!=',False)])
        print("success_pack_lines",success_pack_lines)
        data = []
        user = self.env.user
        is_admin = user.has_group('base.group_system')
        domain = []
        teams = self.env['project.team'].sudo().search([('timesheet_user_ids', '=', user.id)])
        project_obj = self.env['pack.projects'].sudo().search([])
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

        if not is_admin:
            user_ids = teams.mapped('employee_ids').sorted('name')
            domain.append(('user_id', 'in', user_ids.ids))
        elif not is_admin:
            domain.append(('user_ids', '=', user.id))


        for line in success_pack_lines:
            print("rrrrr",line.pack_project_id.start_date.strftime('%d/%m/%Y') )

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
                'worked_hours': self.format_hours(line.pack_project_id.worked_hours),
                # 'utilization': utilization,
                'status': dict(line.pack_project_id._fields['stages'].selection).get(line.pack_project_id.stages),
                'company_id': line.success_pack_id.company_id.id,
            })
        return {'vals': data, 'is_admin': is_admin, 'company_data': company_data, 'projects': projects,
                'packages': packages,'customers': customers, 'status': status, }
