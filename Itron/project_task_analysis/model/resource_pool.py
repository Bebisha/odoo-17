# -*- coding: utf-8 -*-

from datetime import datetime, date

from odoo import models, fields, tools, _, api, Command
from odoo.exceptions import ValidationError, UserError


class ProjectResourcePool(models.Model):
    _name = 'project.resource.pool'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Model for requesting resource in pool"

    name = fields.Char('Name', default=lambda self: _('New'), copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('send', 'Request Send'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('discuss', 'Discuss'),
    ], string='Status', default='draft', tracking=True)

    employee_id = fields.Many2one('hr.employee', 'Employee')
    users_id = fields.Many2one('res.users', 'Requester', required=True, default=lambda self: self.env.user.id)
    engagement_model = fields.Selection([('resource_mnt', 'Resource Management'),
                                         ('bug_fixing', 'Bug Fixing'),
                                         ('documentation', 'Documentation'),
                                         ('development', 'Development'),
                                         ('add_support', 'Add Support'),
                                         ('testing', 'Testing')], string="Engagement Model", required=True)
    created_date = fields.Date('Created Date', default=fields.Date.context_today)
    period = fields.Many2one('kg.period', string="Period")
    user_ids = fields.Many2many('res.users', string='Assignees', required=True)
    res_user_ids = fields.Many2many('res.users', string='Assignees Relation', relation='res_user_rel',
                                    compute='compute_res_user')
    project_task_ids = fields.Many2many('project.task', string='Project Task', copy=False)
    project_id = fields.Many2one('project.project', 'Project', required=True)
    milestone_id = fields.Many2one('project.milestone', 'Milestone',
                                   )
    date_start = fields.Date('Start Date', default=fields.Date.context_today)
    date_end = fields.Date('End Date', required=True)
    date_stop = fields.Date('Stop Date')
    task_ids = fields.One2many('resource.task.line', 'resource_pool_id', string='Task Lines')
    is_approve = fields.Boolean(default=False)
    is_reject = fields.Boolean()
    description = fields.Text("Imp Notes",
                              placeholder="eg:This is a special request for approval. We need this resource ASAP.")
    task_count = fields.Float('Tasks', default=0, compute='compute_task_count', copy=False)
    reject_res = fields.Html('Reject Reason')
    planned_hrs = fields.Float('Planned Hours', compute='compute_planned_hrs', default=0)
    extend_ = fields.Boolean(default=False)
    extend_count = fields.Integer(default=0)
    company_id = fields.Many2one(
        'res.company', string='Company', change_default=True,
        default=lambda self: self.env.company,
        required=False)

    state_display = fields.Char(compute='_compute_state_display', string='State Display')

    @api.onchange('user_ids')
    def _onchange_user_ids(self):
        """
        When user_ids are updated, assign or remove resource_id from task lines.
        - Add resource_id if missing.
        - Remove resource_id if user is removed from user_ids.
        """
        current_user_ids = self.user_ids.ids  # The currently selected users
        task_lines = self.task_ids  # Get all the task lines

        # Check if there are any users selected
        if current_user_ids:
            # 1. Assign resource_id for task lines without it
            for index, task_line in enumerate(task_lines):
                if not task_line.resource_id:
                    # Assign users from user_ids as resource_id for task lines without resource_id
                    if index < len(current_user_ids):
                        task_line.resource_id = current_user_ids[index]
                    else:
                        task_line.resource_id = current_user_ids[0]  # Repeat the first user if not enough users

            # 2. Remove resource_id from task lines if the user is no longer in user_ids
            for task_line in task_lines:
                if task_line.resource_id and task_line.resource_id.id not in current_user_ids:
                    task_line.resource_id = False  # Remove the resource_id if the user is removed
        else:
            # If no users are selected, clear the resource_id for all task lines
            for task_line in task_lines:
                task_line.resource_id = False

    @api.depends('state')
    def _compute_state_display(self):
        for record in self:
            # Convert selection key to display label
            record.state_display = dict(self.fields_get(allfields=['state'])['state']['selection'])[record.state]

    @api.depends('date_start', 'date_end')
    def compute_res_user(self):
        all_users = self.env['res.users'].search([])
        all_task = self.env['project.task'].sudo().search([('date_deadline', '>', self.date_start)])
        # , ('is_closed', '=', False)])
        task_employees = all_task.mapped('user_ids')

        user_ids = all_users.ids
        users_list = []
        for rec in user_ids:
            if rec not in task_employees.ids:
                users_list.append(rec)
        self.res_user_ids = users_list

    @api.depends('task_ids')
    def compute_planned_hrs(self):
        if self.task_ids:
            for rec in self.task_ids:
                self.planned_hrs += rec.planned_hrs
        else:
            self.planned_hrs = 0

    def compute_task_count(self):
        """compute count Tasks"""
        for record in self:
            record.task_count = len(record.sudo().project_task_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """ Create a sequence for the resource pool model """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('rp.reference')
                vals['name'] = sequence
        return super().create(vals_list)

    @api.onchange('date_end', 'date_start')
    def onchange_end(self):
        """validation for dates"""
        if self.date_end:
            if self.date_end < self.date_start:
                raise ValidationError(_('The end date occurs before the start date.'))

    def send_mail(self):
        """Send email to approvers"""
        approval_ids = self.env['ir.config_parameter'].sudo().get_param('project_task_analysis.approval_ids')
        group_send_mail = []

        for config_rec in self.env['res.users'].browse(eval(approval_ids)):
            if config_rec.email:
                group_send_mail.append(config_rec.email)

        subject = _('Resource Allocation Request')

        # Fetch the task names and user names corresponding to the IDs
        task_names = str(
            ["<li>" + task.description + " - " + str(self.hour_format(task.planned_hrs)) + " hrs " + "</li>" for task in
             self.task_ids])
        cleaned_string = task_names.replace("[", "").replace("]", "").replace("', '", "").replace("'", "")
        user_names = [user.name for user in self.user_ids]

        # Create a bulleted list of task names and user names
        task_names_list = cleaned_string
        users_list = ", ".join(user_names)

        body = _(
            '''
            <p>Hi Sir/Madam,</p>
            <p>You have received a resource request for the project "<strong>%s</strong>" by <strong>%s</strong>. Here are the details:</p>
             <p><strong>Date: From %s to %s </strong></p>
            <p><strong>Resource:</strong> %s</p>
            <p><strong>Planned Hours:</strong> %s hours</p>
            <p><strong>Tasks:</strong><br/><ul>%s</ul></p>
            <p>%s</p>
            <p>Please review the details and take the necessary action by clicking on one of the options below:</p>
            '''
        ) % (
                   self.sudo().project_id.name,
                   self.users_id.name,
                   str(self.date_start),
                   str(self.date_end),
                   users_list,
                   self.hour_format(self.planned_hrs),
                   task_names_list,
                   self.description if self.description else ''
               )

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        # approve_url = "{}/project_task_analysis/approve_task?record_id={}".format(base_url, self.id)
        # discuss_url = "{}/project_task_analysis/discuss_task?record_id={}".format(base_url, self.id)
        reject_url = "{}/web#id={}&view_type=form&model={}".format(base_url, self.id, self._name)

        html_content = """
            <div>
                <a href="{}">
                    <button style='padding:7px;background-color:#71639e;color:white;height:35px;border-radius:10px;'>
                        VIEW REQUEST
                    </button>
                </a>
            </div>
        """.format(reject_url)

        outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        email_from = outgoing_mail_server.sudo().smtp_user

        mail_values = {
            'subject': subject,
            'body_html': body + "<br/>" + html_content,
            'email_to': ', '.join(group_send_mail),
            'email_from': email_from,
        }

        # Send the email
        self.env['mail.mail'].sudo().create(mail_values).send()

    def hour_format(self, hrs):
        hours = int(hrs)
        minutes = int((hrs - hours) * 60)
        formatted_hrs = f"{hours}:{minutes:02d}"
        return formatted_hrs

    def request_send(self):

        """button for request"""

        self.write({
            'state': 'send'
        })

        if self.state == 'send':
            self.send_mail()

    def button_approve(self):
        """button for approve"""

        team = self.env['project.team'].sudo().search([('employee_ids', 'in', self.user_ids.ids)])

        for rec in team:
            """to remove from  resource pool team"""
            if rec.sudo().is_resource_pool:
                for user in self.user_ids:
                    rec.sudo().write({'employee_ids': [Command.unlink(user.id)]})
        # c_team = self.project_id.project_team_id
        """to include project team"""
        odoo_team = self.env['project.team'].sudo().search([('is_odoo', '=', True)])
        if odoo_team and self.date_start == date.today():
            for user in self.user_ids:
                odoo_team.sudo().write({'employee_ids': [Command.link(user.id)]})
        if not odoo_team:
            raise ValidationError('Please create an odoo team !!')

        for rec in self.task_ids:
            """To create task"""
            if not rec.task_id:
                development = rec.task_type
                task = self.env['project.task'].sudo().create({
                    'name': rec.description,
                    'user_ids': [(6, 0, rec.resource_id.ids)],
                    'project_id': self.sudo().project_id.id,
                    'date_start': rec.start_date,
                    'date_deadline': rec.end_date if rec.end_date else datetime.now(),
                    'allocated_hours': rec.planned_hrs,
                    'task_type': development,
                    'description': rec.task_description,
                    'resource_id': self.id,
                    # 'milestone_ids': self.milestone_id.id,
                    'milestone_ids': rec.milestone_id.id,
                    'time_line_id': rec.time_line_id.id,
                    'is_main_task': True,
                    'company_id': rec.resource_id.company_id.id if rec.resource_id.company_id else False,

                })
                rec.sudo().task_id |= task
                self.sudo().project_task_ids |= task
            else:
                rec.sudo().task_id.write({
                    'allocated_hours': rec.planned_hrs,
                    'date_deadline': rec.end_date,
                })
        resource_pool_obj = self.env['project.team'].sudo().search([('is_resource_pool', '=', True)], limit=1)
        pool_lines = resource_pool_obj.pool_lines.filtered(lambda x: x.resource_id.id in self.user_ids.ids)
        resource_ids = pool_lines.mapped('resource_id').ids
        if resource_ids:
            team = self.env['project.team'].sudo().search([('employee_ids', 'in', resource_ids)])
            team.sudo().write({'employee_ids': [(3, resource_id) for resource_id in resource_ids]})
            odoo_obj = self.env['project.team'].sudo().search([('is_odoo', '=', True)], limit=1)
            odoo_obj.sudo().write({'employee_ids': [(4, resource_id) for resource_id in resource_ids]})
        pool_lines.unlink()
        for usr in self.user_ids:
            task_line = self.sudo().task_ids.filtered(lambda x: x.resource_id.id == usr.id)

            if task_line:
                min_date = min(task_line.mapped('start_date'))
                max_date = max(task_line.mapped('end_date'))
                today = date.today()
                existing_allocation = self.env['kg.resource.allocation'].sudo().search([
                    ('resource_id', '=', usr.id),
                    ('end_date', '<=', today)
                ], limit=1)

                if self.date_end <= today:
                    print(self.date_end, " self.date_end self.date_end")
                    if existing_allocation:
                        existing_allocation.sudo().write({
                            'team_id': resource_pool_obj.id,
                            'project_id': self.sudo().project_id.id,
                            'team_lead_id': self.sudo().project_id.user_id.id,
                            'engagement_model': self.engagement_model,
                            'period': self.period.id,
                            'start_date': self.date_start,
                            'end_date': self.date_end,
                            'planned_hrs': self.planned_hrs,
                            'comments': self.description,
                        })
                    else:
                        val = {
                            'team_id': resource_pool_obj.id,
                            'resource_id': usr.id,
                            'project_id': self.sudo().project_id.id,
                            'team_lead_id': self.project_id.sudo().user_id.id,
                            'engagement_model': self.engagement_model,
                            'period': self.period.id,
                            'start_date': min_date,
                            'end_date': max_date,
                            'planned_hrs': self.planned_hrs,
                            'comments': self.description,
                        }
                        self.env['kg.resource.allocation'].sudo().create(val)
                else:
                    val = {
                        'team_id': resource_pool_obj.id,
                        'resource_id': usr.id,
                        'project_id': self.sudo().project_id.id,
                        'team_lead_id': self.project_id.sudo().user_id.id,
                        'engagement_model': self.engagement_model,
                        'period': self.period.id,
                        'start_date': min_date,
                        'end_date': max_date,
                        'planned_hrs': self.planned_hrs,
                        'comments': self.description,
                    }
                    self.env['kg.resource.allocation'].sudo().create(val)

        self.sudo().write({
            # 'is_approve': True,
            'state': 'approve',
            'extend_': False
        })

        # self.send_mail()

    def button_discuss(self):
        self.sudo().write({
            'state': 'discuss'
        })

    def button_confirm(self):
        # today = date.today()
        # conflicting_resources = []
        for record in self:
            # for task in record.task_ids:
            #     if task.resource_id:
            #         existing_allocation = self.env['kg.resource.allocation'].search([
            #             ('resource_id', '=', task.resource_id.id),
            #             ('start_date', '<=', task.end_date),
            #             ('end_date', '>=', task.start_date),
            #             ('status', 'not in', ['completed', 'hold'])
            #         ])
            #
            #         print(existing_allocation, "existing_allocation for", task.resource_id.name)
            #
            #         if existing_allocation:
            #             conflicting_resources.append(
            #                 f"Resource '{task.resource_id.name}' is already allocated in another request."
            #             )

            # for user in record.user_ids:
            #     assigned_tasks = self.env['project.task'].search([
            #         ('user_ids', 'in', user.id),
            #         ('date_deadline', '>=', today),
            #         # ('id', 'not in', record.project_task_ids.ids),
            #         # ('stage_id.is_check_task_status', '=', True)
            #     ])
            #
            #     print(assigned_tasks, 'assigned_tasks for', user.name)
            #     if assigned_tasks:
            #         task_details = []
            #         for task in assigned_tasks:
            #             task_name = task.project_id.name or "N/A"
            #             task_deadline = task.date_deadline or "No deadline"
            #             task_details.append(f"Project '{task_name}' (Deadline: {task_deadline})")
            #             print(task_name, "ewewe")
            #
            #         task_list = "\n  - ".join(task_details)
            #         conflicting_resources.append(
            #             f"Resource '{user.name}' is assigned to the following project:\n  - {task_list}"
            #         )
            #
            # if conflicting_resources:
            #     conflict_message = "\n\n".join(conflicting_resources)
            #     raise ValidationError(
            #         f"Some resources are already assigned to other projects:\n{conflict_message}"
            #     )

            if not record.task_ids:
                raise ValidationError("There is no task line in this request")
            record.state = 'confirm'

    def button_reject(self):
        """button for reject wizard"""
        # wizard = self.env['project.reject.reason'].create({'resource_id': self.id})
        return {
            'name': _('Reject  Wizard'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.reject.reason',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'context': {'default_resource_id': self.id,
                        'from_dashboard': self.env.context.get('from_dashboard', False), },
            'target': 'new',
        }

    def view_resource_pool(self):
        resource_pool_obj = self.env['project.team'].sudo().search([('is_resource_pool', '=', True)], limit=1)
        return {
            'name': _('View Resource'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.team',
            'view_mode': 'form',
            'view_id': [self.env.ref('project_task_analysis.project_team_view_resource_pool').id],
            'res_id': resource_pool_obj.id,
            'target': 'current',
        }

    def button_extend(self):
        """button for reject wizard"""
        # wizard = self.env['extended.resource'].create({'resource_id': self.id})
        # if self.extend_count >= 3:
        #     raise ValidationError('You cannot extend this request further. You can create new request and send it for approval !')

        return {
            'name': _('Resource Allocation Extension'),
            'type': 'ir.actions.act_window',
            'res_model': 'extended.resource',
            'view_mode': 'form',
            'context': {'default_resource_id': self.id},
            # 'res_id': wizard.id,
            'target': 'new',
        }

    def action_resource_allocation(self):
        # resource_pool_obj = self.env['project.team'].search([('is_resource_pool', '=', True)], limit=1)
        resource_pool_obj = self.env['project.team'].sudo().search([('is_resource_pool', '=', True)], limit=1)
        odoo_obj = self.env['project.team'].sudo().search([('is_odoo', '=', True)], limit=1)
        if resource_pool_obj:
            allocation_lines = resource_pool_obj.allocation_lines.filtered(
                lambda x: x.end_date and x.end_date < date.today()
            )
            resource_ids = allocation_lines.mapped('resource_id').ids
            if resource_ids:
                team = self.env['project.team'].sudo().search([('employee_ids', 'in', resource_ids)])
                if team:
                    team.write({'employee_ids': [(3, resource_id) for resource_id in resource_ids]})
                resource_pool_obj.write({'employee_ids': [(4, resource_id) for resource_id in resource_ids]})
            for aln in allocation_lines:
                existing_records = self.env['resource.pool'].sudo().search([
                    ('team_id', '=', resource_pool_obj.id),
                    ('resource_id', '=', aln.resource_id.id)
                ])
                if not existing_records:
                    val = {
                        'team_id': resource_pool_obj.id,
                        'resource_id': aln.resource_id.id,
                    }
                    self.env['resource.pool'].sudo().create(val)
            allocation_lines.unlink()
        if odoo_obj:
            members = resource_pool_obj.allocation_lines.mapped('resource_id')
            odoo_obj.sudo().write({'employee_ids': [Command.link(member_id) for member_id in members.ids]})

    def action_task_end_date_over(self):
        """action for schedule action for ending date"""
        resource = self.env['project.resource.pool'].sudo().search([('date_end', '=', date.today())])
        resource_start = self.env['project.resource.pool'].sudo().search([('date_start', '=', date.today())])
        for rec in resource:
            team = self.env['project.team'].sudo().search([('employee_ids', 'in', rec.user_ids.ids)])
            resource_team = self.env['project.team'].sudo().search([('is_resource_pool', '=', True)])
            team.sudo().write({'employee_ids': [Command.unlink(rec.user_ids.ids)]})
            if resource_team:
                resource_team.sudo().write({'employee_ids': [Command.link(rec.user_ids.ids)]})

            subject = _('Resource Requisition Date Ended for : %s') % rec.user_ids.name
            body = _('Resource Requisition Date Ended for : %s') % rec.user_ids.name

            outgoing_mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
            email_from = outgoing_mail_server.sudo().smtp_user
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': rec.users_id.email,
                'email_from': email_from,
            }
            rec.env['mail.mail'].create(mail_values).send()
        for rec in resource_start:
            team = self.env['project.team'].sudo().search([('employee_ids', 'in', rec.users_id.id)])
            odoo_team = self.env['project.team'].sudo().search([('is_odoo', '=', True)])
            team.sudo().write({'employee_ids': [Command.unlink(rec.users_id.id)]})
            if odoo_team:
                odoo_team.write({'employee_ids': [Command.link(rec.users_id.id)]})

    def show_task(self):
        """show tasks"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'view_mode': 'tree,form',  # Specify view modes as a list
            'res_model': 'project.task',
            'domain': [('id', 'in', self.sudo().project_task_ids.ids)],
            # 'context': {'create': False}  # Context should be a dictionary
        }

    def request_again(self):
        """Request Again Button"""
        self.write({
            'state': 'draft'
        })


class ProjectResourceTaskLine(models.Model):
    _name = 'resource.task.line'
    """Model for resource pool task line"""

    resource_pool_id = fields.Many2one('project.resource.pool')
    resource_id = fields.Many2one('res.users', string="Resource", required=True)
    description = fields.Char('Task')
    start_date = fields.Date('Start Date', default=fields.Date.context_today)
    end_date = fields.Date('End Date')
    planned_hrs = fields.Float('Planned hours', required=True)
    task_id = fields.Many2one('project.task')
    extend_hrs = fields.Float('Extend Hrs')
    extended_id = fields.Many2one('extended.resource')
    ext_bool = fields.Boolean(default=False)
    time_line_id = fields.Many2one('timeline.line', string="Activity")
    milestone_id = fields.Many2one('project.milestone', string="Milestone")
    mdlname_id = fields.Many2one('project.tags', 'Module', domain=[('is_module', '=', True)])
    task_type = fields.Selection(
        string='Task Type',
        selection=[
            ('development', 'Development'),
            ('bug', 'Bug'),
            ('cr', 'Change Request'),
            ('investigation', 'Investigation'),
            ('development', 'Development'),
            ('enhance', 'Enhancement'), ],
        default='development')
    task_description = fields.Html(string="Description")


    @api.model
    def create(self, vals):
        record = super(ProjectResourceTaskLine, self).create(vals)
        if vals.get('planned_hrs', 0.0) == 0.0:
            raise ValidationError("Please enter Planned Hours.")

        # Check if 'resource_id' is in the values to be created
        if 'resource_id' in vals and vals.get('resource_id'):
            users_ids = record.resource_pool_id.user_ids.ids

            # Add the resource_id to user_ids if it's not already present
            if vals['resource_id'] not in users_ids:
                print("Adding resource to user_ids during create")
                record.resource_pool_id.sudo().write({'user_ids': [(4, vals['resource_id'])]})

        return record

    def write(self, vals):
        result = super(ProjectResourceTaskLine, self).write(vals)
        if 'resource_id' in vals:
            users_ids = self.resource_pool_id.user_ids.ids
            if self.resource_id.id not in users_ids:
                self.resource_pool_id.sudo().write({'user_ids': [(4, self.resource_id.id)]})
            if not self.resource_id:
                self.resource_pool_id.sudo().write({'user_ids': [(3, self.resource_id.id)]})
            print(self.resource_pool_id.sudo().user_ids.ids, "self.resource_pool_id.user_ids.ids")
        return result

    # @api.onchange('resource_id')
    # def _onchange_resource_pool_id(self):
    #     """To get the resource that already choose in the assignee"""
    # if self.resource_pool_id:
    #     user_ids = self.resource_pool_id.user_ids.ids
    #     return {
    #         'domain': {'resource_id': [('id', 'in', user_ids)]}
    #     }
    # else:
    #     return {
    #         'domain': {'resource_id': []}
    #     }

    @api.onchange('end_date')
    def validation_date(self):
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError('End date is less than Start date')
            if self.resource_pool_id.date_end:
                if self.end_date > self.resource_pool_id.date_end:
                    raise ValidationError('End date is greater than Allocation date')


class ProjectStage(models.Model):
    _inherit = 'project.task.type'


class ProjectTag(models.Model):
    _inherit = 'project.tags'

    is_module = fields.Boolean(string="Is Module", default=False)
