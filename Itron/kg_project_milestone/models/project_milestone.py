# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime

from odoo.exceptions import ValidationError


class Milestone(models.Model):
    _inherit = 'project.milestone'

    def view_tasks(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('project.action_view_all_task').sudo().read()[0]
        action['domain'] = [('milestone_ids', '=', self.id)]
        return action



class ProjectMilestone(models.Model):
    _name = 'kg.project.timeline'
    _description = 'kg Project Timeline'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('project.project', 'Project', required=True)
    start_date = fields.Date("Start Date")
    milestone_line_ids = fields.One2many('timeline.line', 'project_id', string='Milestone Lines', copy=True)
    milestone_line_ids_new = fields.One2many('timeline.line', 'project_id', string='Milestone Lines', copy=False,
                                             compute='compute_milestones')
    milestone_line_sec_ids = fields.One2many('timeline.line.sec', 'project_id', string='Milestone Lines', copy=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancel', 'Cancel')],
        string="Status", default='draft')
    active = fields.Boolean(default=True)
    week_start = fields.Selection(
        [('sunday', 'Sunday'), ('monday', 'Monday')],
        string="Week Start", default='monday')
    add_remark = fields.Boolean(string='Add Remarks in Printout', default=False)

    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda x: x.env.company, readonly=True,
        required=True)

    assignees_list = fields.Many2many('res.users', string="Assignees", readonly=False,
                                      compute="compute_assignees_task", inverse="inverse_assignees_task", )

    task_count = fields.Integer(compute='_compute_task_count', string='Task')
    allowed_company_ids = fields.Many2many('res.company',relation='rec_company_ids',string='Visible Companies')

    def action_view_filter_lines(self):
        """ Filter milestone lines to easily view them based on their status."""
        tree = self.env.ref('kg_project_milestone.kg_time_line_tree_view_id', False)
        milestone_ids = []
        for timeline in self:
            for lines in timeline.milestone_line_ids:
                if not lines.display_type:
                    milestone_ids.append(lines.id)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lines',
            'view_mode': 'tree',
            'view_id': tree.id,
            'res_model': 'timeline.line',
            'context': "{'create':False}",
            'domain': [('id', 'in', milestone_ids)]
        }

    def _compute_task_count(self):
        for timeline in self:
            tasks = self.env['project.task'].search(
                [('project_id', '=', self.name.id), ('stage_id.is_closed', '!=', True)])
            timeline.task_count = len(tasks)

    def action_view_tasks(self):
        self.ensure_one()
        tree_view_id = self.env.ref('kg_project_milestone.kg_project_stages_group').id
        form_view_id = self.env.ref('project.view_task_form2').id

        return {
            'name': 'Tasks',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'tree,form',
            'views': [
                [tree_view_id, 'tree'],
                [form_view_id, 'form']
            ],
            'domain': [('project_id', '=', self.name.id), ('stage_id.is_closed', '!=', True)],
            'context': {
                'group_by': 'stage_id',
            },
        }

    @api.depends('name')
    def compute_assignees_task(self):
        for rec in self:
            rec.assignees_list = rec.name.mapped('task_ids.user_ids')

    def inverse_assignees_task(self):
        for rec in self:
            all_task_users = rec.name.mapped('task_ids.user_ids')
            users_to_remove = all_task_users - rec.assignees_list
            users_to_add = rec.assignees_list - all_task_users

            for task in rec.name.task_ids:
                task.user_ids = [(3, user.id) for user in users_to_remove]
                task.user_ids = [(4, user.id) for user in users_to_add]

    def update_time_line(self):

        # Get all records from kg.project.timeline

        for record in self:
            # Loop through each record in milestone_line_ids
            record.milestone_line_sec_ids.unlink()
            for rec in record.milestone_line_ids:
                # Determine if the record is a section
                if rec.display_type == 'line_section':
                    is_section = True
                else:
                    is_section = False

                # Prepare the data to be copied
                data = {
                    'sequence': rec.sequence,
                    'name': rec.name,
                    'milestone_id': rec.milestone_id.id,
                    'days': rec.days,
                    'line_start_date': rec.line_start_date,
                    'line_end_date': rec.line_end_date,
                    'overlap': rec.overlap,
                    'is_section': is_section,  # Set is_section based on display_type
                    'is_sub_task': rec.is_sub_task,
                    'state_1': rec.state_1,
                    'state': rec.state,
                    'project_id': rec.project_id.id,
                    'done_date': rec.done_date,
                    'is_done': rec.is_done,
                }
                # Add data to milestone_line_sec_ids
                record.write({'milestone_line_sec_ids': [(0, 0, data)]})

    # def upload_milestone_line(self):
    #     return {
    #         'name': _('Update Milestone Lines'),
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'update.milestone.wizard',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_update_id': self.id,
    #         }
    #     }

    def sort_order_lines(self):
        # Extracting milestone lines and sorting based on sequence, with False values last
        sorted_milestones = sorted(self.milestone_line_sec_ids,
                                   key=lambda rec: (rec.sequence is False, rec.sequence or ''))
        sorted_milestones_recordset = self.env['timeline.line.sec'].browse([rec.id for rec in sorted_milestones])

        # Clear existing data in the one2many field (optional)
        self.write({'milestone_line_sec_ids': [(5, 0, [])]})  # This clears existing lines

        # Write the new data to the one2many field
        for record in sorted_milestones_recordset:
            data = {
                'sequence': record.sequence,
                'name': record.name,
                'is_section': record.is_section,
            }
            if not record.is_section:
                data.update({
                    'milestone_id': record.milestone_id.id,
                    'days': record.days,
                    'line_start_date': record.line_start_date,
                    'line_end_date': record.line_end_date,
                    'overlap': record.overlap,
                    'is_sub_task': record.is_sub_task,
                    'state_1': record.state_1,
                    'state': record.state,
                    'project_id': record.project_id.id,
                    'done_date': record.done_date,
                    'is_done': record.is_done,
                    # Add other fields you want to write
                })

            self.write({'milestone_line_sec_ids': [(0, 0, data)]})

    def create_subsequence_a(self, new_sub_seq):
        new_line = self.env['timeline.line.sec'].create({
            'project_id': self.id,
            'sequence': new_sub_seq,
            'is_sub_task': True,
        })

    @api.depends('milestone_line_ids')
    def compute_milestones(self):
        for record in self:
            filtered_lines = record.milestone_line_ids.filtered(lambda line: not line.is_sub_task)
            record.milestone_line_ids_new = [(6, 0, filtered_lines.ids)]

    # Revision Functionality
    @api.depends("old_revision_ids")
    def _compute_has_old_revisions(self):
        for rec in self:
            rec.has_old_revisions = (
                True if rec.with_context(active_test=False).old_revision_ids else False
            )

    revision_number = fields.Integer(string="Revision", copy=False, default=0)
    current_revision_id = fields.Many2one(
        comodel_name="kg.project.timeline",
    )
    old_revision_ids = fields.One2many(
        comodel_name="kg.project.timeline",
        inverse_name="current_revision_id",
        string="Old revisions",
        readonly=True,
    )

    has_old_revisions = fields.Boolean(compute="_compute_has_old_revisions")
    revision_count = fields.Integer(
        compute="_compute_revision_count", string="Previous versions count"
    )

    @api.depends("old_revision_ids")
    def _compute_revision_count(self):
        res = self.with_context(active_test=False).read_group(
            domain=[("current_revision_id", "in", self.ids)],
            fields=["current_revision_id"],
            groupby=["current_revision_id"],
        )
        revision_dict = {
            x["current_revision_id"][0]: x["current_revision_id_count"] for x in res
        }
        for rec in self:
            rec.revision_count = revision_dict.get(rec.id, 0)

    def button_in_progress(self):
        self.write({'state': 'in_progress'})

    def button_completed(self):
        self.write({'state': 'completed'})

    def button_compute(self):
        for rec in self.milestone_line_ids:
            pass
        if self.milestone_line_ids and not self.start_date:
            if self.milestone_line_ids[0].line_start_date:
                self.start_date = self.milestone_line_ids[0].line_start_date
        if self.start_date and self.milestone_line_ids:
            start_date = self.start_date
            week_start = self.week_start
            for line in self.milestone_line_ids.sorted(lambda c: c.sequence):
                if line.state == 'completed':
                    start_date = line.line_end_date + datetime.timedelta(days=1)
                elif line.state == 'pending':
                    line.line_start_date = start_date
                    current_date = start_date
                    business_days_to_add = line.days
                    while business_days_to_add > 0:
                        weekday = current_date.weekday()
                        current_date += datetime.timedelta(days=1)
                        if week_start == 'sunday' and weekday in [4, 5]:  # monday = 0, sunday = 6
                            continue
                        if week_start == 'monday' and weekday in [5, 6]:  # sunday = 6
                            continue
                        business_days_to_add -= 1

                    line.line_end_date = current_date - datetime.timedelta(days=1)
                    if line.overlap:
                        continue
                    if current_date.weekday() >= 5:
                        current_date += datetime.timedelta(days=1)
                        if current_date.weekday() >= 5:
                            current_date += datetime.timedelta(days=1)
                    start_date = current_date

    # Revision

    # @api.returns("self", lambda value: value.id)
    # def copy(self, default=None):
    #     default = default or {}
    #     rec = super().copy(default=default)
    #     return rec

    def _get_new_rev_data(self, new_rev_number):
        self.ensure_one()
        return {
            "old_revision_ids": [(4, self.id, False)],
        }

    def _prepare_revision_data(self, new_revision):
        return {"active": False, "current_revision_id": new_revision.id, "state": "cancel"}

    def action_view_revisions(self):
        self.ensure_one()
        action = self.env.ref("kg_project_milestone.kg_project_timeline_menu_action")
        result = action.read()[0]
        result["domain"] = [("active", "=", False), ('name', '=', self.name.id)]
        result["context"] = {
            "active_test": 0,
            "search_default_current_revision_id": self.id,
            "default_current_revision_id": self.id,
        }
        return result

    def copy_revision_with_context(self):
        default_data = self.default_get([])
        new_rev_number = self.revision_number + 1
        vals = self._get_new_rev_data(new_rev_number)
        default_data.update(vals)
        new_revision = self.copy(default_data)
        self.old_revision_ids.write({"current_revision_id": new_revision.id})
        self.write(self._prepare_revision_data(new_revision))
        return new_revision

    def create_revision(self):
        revision_ids = []
        # Looping over records
        for rec in self:
            # Calling  Copy method
            copied_rec = rec.copy_revision_with_context()
            if hasattr(self, "message_post"):
                msg = _("New revision created: %s") % copied_rec.name
                copied_rec.message_post(body=msg)
                rec.message_post(body=msg)
            revision_ids.append(copied_rec.id)
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "name": _("New Revisions"),
            "res_model": self._name,
            "domain": "[('id', 'in', %s)]" % revision_ids,
            "target": "current",
        }
        return action

    def create_subsequence(self, new_sub_seq):
        new_line = self.env['timeline.line'].create({
            'project_id': self.id,
            'sequence': new_sub_seq,
            'is_sub_task': True,

        })


class TimelineLine(models.Model):
    _name = 'timeline.line'
    _description = 'Timeline Line'

    name = fields.Char()
    milestone_id = fields.Many2one('project.milestone', string='Milestone' ,copy=False)
    # sequence = fields.Integer(string='Sequence', default=10)
    widget_seq = fields.Char(string='Seq', default=10)
    sequence = fields.Char(string='Sequence')
    project_id = fields.Many2one('kg.project.timeline', 'Timeline')
    project_rel_id = fields.Many2one(related='project_id.name')
    description = fields.Text("Description")
    days = fields.Integer("Days")
    days_spent_hrs = fields.Char('Days Spent', compute='compute_days_spent')
    line_start_date = fields.Date("Start Date")
    line_end_date = fields.Date("End Date")
    overlap = fields.Boolean(string="Overlap", copy=True, default=False)
    state = fields.Selection([('pending', 'Pending'), ('completed', 'Completed')], string="Status", default='pending',
                             copy=True)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False,
                                    help="Technical field for UX purpose.")
    state_1 = fields.Selection([('open', 'Open'), ('inprogress_b', 'In progress'), ('inprogress_o', 'In progress'),
                                ('inprogress_r', 'In progress')
                                   , ('completed_g', 'Completed'), ('completed_r', 'Completed')], string="Status",
                               default='open',
                               compute='compute_state', store=True
                               )

    done_date = fields.Date('Done Date')
    completed_date = fields.Date('Completed Date')
    is_done = fields.Boolean(string='Is Done', default=False)
    remark = fields.Text(string='Remarks')

    is_sub_task = fields.Boolean('Sub')

    user_ids = fields.Many2many('res.users', string='Userss')

    def compute_days_spent(self):
        def float_hours_to_hhmm(float_hours):
            hours = int(float_hours)
            minutes = int(round((float_hours - hours) * 60))
            return f"{hours:02d}:{minutes:02d}"

        for rec in self:
            tasks = rec.env['project.task'].search([('time_line_id', '=', rec.id)])
            if tasks:
                total_hours = sum(tasks.mapped('effective_hours'))
                days = int(total_hours // 8)
                remaining_hours = total_hours % 8

                # Convert remaining float hours (e.g. 3.75) to HH:MM format
                time_str = float_hours_to_hhmm(remaining_hours)

                print("total_hours", total_hours)

                if days > 0 and remaining_hours > 0:
                    rec.days_spent_hrs = f"{days} day{'s' if days > 1 else ''} {time_str} hrs"
                elif days > 0:
                    rec.days_spent_hrs = f"{days} day{'s' if days > 1 else ''}"
                elif remaining_hours > 0:
                    rec.days_spent_hrs = f"{time_str} hrs"
                else:
                    rec.days_spent_hrs = "0 hrs"
            else:
                rec.days_spent_hrs = "0 hrs"

    @api.model
    def scheduled_action_email(self):
        """Scheduled action for sending mail when line_end_date is one day before the current date."""
        current_date = fields.Date.today()
        target_date = current_date + datetime.timedelta(days=1)
        records = self.search([('line_end_date', '=', target_date)])

        for record in records:
            group_send_mail = []

            for user in record.user_ids:
                if user.email:
                    group_send_mail.append(user.email)

            if not group_send_mail:
                continue

            subject = _('Timeline EndDate is Tomorrow for : %s') % record.name

            body = _('''
                        Timeline end date is near for : %s
                               ''') % (
                record.name,
            )

            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': ', '.join(group_send_mail),
            }

            # Send the email
            self.env['mail.mail'].create(mail_values).send()

    @api.onchange('line_end_date', 'line_start_date', 'completed_date')
    def onchange_date_validation(self):
        if self.line_end_date and self.line_start_date:
            if self.line_end_date < self.line_start_date:
                raise ValidationError('Start date must be before End date')
        if self.completed_date and self.line_start_date:
            if self.completed_date < self.line_start_date:
                raise ValidationError('Completed date must be After Start date')

    @api.depends('line_end_date', 'line_start_date', 'is_done', 'done_date', 'completed_date')
    def compute_state(self):
        current_date = datetime.date.today()
        for rec in self:
            if rec.is_done:
                comparison_date = rec.line_end_date
                rec.state_1 = 'completed_g' if comparison_date and rec.done_date and comparison_date >= rec.done_date else 'completed_r'
            elif rec.line_start_date and rec.line_end_date:
                if rec.line_start_date > current_date:
                    rec.state_1 = 'open'
                else:
                    two_days_before_end_date = rec.line_end_date - datetime.timedelta(days=2)
                    if current_date >= two_days_before_end_date and current_date <= rec.line_end_date:
                        rec.state_1 = 'inprogress_o'
                    elif rec.line_end_date < current_date:
                        rec.state_1 = 'inprogress_r'
                    else:
                        rec.state_1 = 'inprogress_b'
            else:
                rec.state_1 = 'open' if not rec.line_start_date or rec.line_start_date > current_date else 'inprogress_b'

    def done_click(self):
        for rec in self:
            rec.state = 'completed'
            rec.is_done = True
            if rec.completed_date:
                rec.done_date = rec.completed_date
            else:
                rec.done_date = datetime.date.today()
            rec.compute_state()

    def reset_click(self):
        for rec in self:
            rec.state = 'pending'
            rec.is_done = False
            rec.compute_state()

    def refresh_click(self):
        for line in self:
            if line.state == 'completed':
                continue
            else:
                week_start = line.project_id.week_start
                line_start_date = line.line_start_date
                business_days_to_add = line.days
                while business_days_to_add > 0:
                    weekday = line_start_date.weekday()
                    line_start_date += datetime.timedelta(days=1)
                    if week_start == 'sunday' and weekday in [4, 5]:  # monday = 0, sunday = 6
                        continue
                    if week_start == 'monday' and weekday in [5, 6]:  # sunday = 6
                        continue
                    business_days_to_add -= 1

                line.line_end_date = line_start_date - datetime.timedelta(days=1)
    def view_tasks(self):
        action = {
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "name": _("Tasks"),
            "res_model": 'project.task',
            "domain": "[('time_line_id', '=', %s)]" % self.id,
            'context': {
                'default_project_id': self.project_id.name.id,
                'default_milestone_ids': self.milestone_id.id,
                'default_time_line_id': self.id,
            },
            "target": "current",
        }
        return action

    def create_project_update(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Project Update',
            'res_model': 'project.update',
            'view_mode': 'form',
            'view_id': False,
            'res_id': False,
            'target': 'current',
            'context': {
                'default_project_id': self.project_id.name.id,
                'default_milestone_id': self.milestone_id.id,
                'default_time_line_id': self.id,
            },
        }

    def view_created_updates(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'View Project Updates',
            'res_model': 'project.update',
            'view_mode': 'tree,form',
            'context': {
                'active_id': self.project_id.name.id,
                'default_milestone_id': self.milestone_id.id,
                'default_time_line_id': self.id,

            },
            'domain': [
                # ('project_id', '=', self.project_id.id),
                ('milestone_id', '=', self.milestone_id.id),
                ('time_line_id', '=', self.id),
            ],
            'target': 'current',
        }

    @api.onchange('line_end_date', 'line_start_date')
    def _onchange_line_end_date(self):
        for line in self:
            if line.state == 'completed':
                continue
            if line.line_start_date and line.line_end_date:
                start_date = line.line_start_date
                end_date = line.line_end_date
                delta = end_date - start_date
                business_days = 0
                for i in range(delta.days + 1):
                    day = start_date + datetime.timedelta(days=i)
                    if day.weekday() < 5:
                        business_days += 1
                line.days = business_days
            else:
                line.days = 0

    new_seq = fields.Integer(default=1)

    def create_subsequence_call(self):
        if self.sequence:
            new_sub_seq = self.sequence + "." + str(self.new_seq)
            self.new_seq += 1
            self.project_id.create_subsequence(new_sub_seq)
        else:
            raise ValidationError('Please add sequence !!!')

    def unlink(self):
        vals = self.env['timeline.line']
        for rec in self:
            if rec.sequence:
                sub_records = self.env['timeline.line'].search([('sequence', 'like', rec.sequence + ".%")])
                vals |= sub_records
        if vals:
            vals.with_context(bypass_recursive_unlink=True).unlink()
        return super(TimelineLine, self).unlink()

    def _bypass_recursive_unlink(self):
        context = self.env.context
        if context.get('bypass_recursive_unlink'):
            return super(TimelineLine, self).unlink()
        return self


class TimelineLineSec(models.Model):
    _name = 'timeline.line.sec'
    _description = 'Timeline Line Second'

    name = fields.Char()
    milestone_id = fields.Many2one('project.milestone', string='Milestone',copy=False)
    widget_seq = fields.Char(string='Seq', default=10)
    sequence = fields.Char(string='Sequence')
    project_id = fields.Many2one('kg.project.timeline', 'Timeline')
    description = fields.Text("Description")
    days = fields.Integer("Days")
    line_start_date = fields.Date("Start Date")
    line_end_date = fields.Date("End Date")
    overlap = fields.Boolean(string="Overlap", copy=True, default=False)
    is_section = fields.Boolean(string="Section", copy=True, store=True, default=False)
    state = fields.Selection([('pending', 'Pending'), ('completed', 'Completed')], string="Status", default='pending',
                             copy=True)
    display_type = fields.Selection([('line_section', "Section"), ('line_note', "Note")], default=False,
                                    help="Technical field for UX purpose.")

    state_1 = fields.Selection([('open', 'Open'), ('inprogress_b', 'In progress'), ('inprogress_o', 'In progress'),
                                ('inprogress_r', 'In progress')
                                   , ('completed_g', 'Completed'), ('completed_r', 'Completed')], string="Status",
                               default='open',
                               compute='compute_state'
                               )

    done_date = fields.Date('Done Date')
    completed_date = fields.Date('Completed Date')
    is_done = fields.Boolean(string='Is Done', default=False)

    is_sub_task = fields.Boolean('Sub')

    is_sunday = fields.Boolean(string="Is Sunday", compute="_compute_is_sunday")
    is_sunday_end = fields.Boolean(string="Is Sunday", compute="_compute_is_sunday_2")

    user_ids = fields.Many2many('res.users', string='Userss')

    @api.model
    def scheduled_action_email(self):
        """Scheduled action for sending mail when line_end_date is one day before the current date."""
        current_date = fields.Date.today()
        target_date = current_date + datetime.timedelta(days=1)
        records = self.search([('line_end_date', '=', target_date)])

        for record in records:
            group_send_mail = []

            for user in record.user_ids:
                if user.email:
                    group_send_mail.append(user.email)

            if not group_send_mail:
                continue

            subject = _('Timeline EndDate is Tomorrow for : %s') % record.name

            body = _('''
                    Timeline end date is near for : %s
                           ''') % (
                record.name,
            )

            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': ', '.join(group_send_mail),
            }

            # Send the email
            self.env['mail.mail'].create(mail_values).send()

    @api.depends('line_end_date')
    def _compute_is_sunday_2(self):
        for record in self:
            if record.line_end_date:
                date = fields.Date.from_string(record.line_end_date)
                record.is_sunday_end = date.weekday() == 6  # Sunday is 6
            else:
                record.is_sunday_end = False

    @api.depends('line_start_date')
    def _compute_is_sunday(self):
        for record in self:
            if record.line_start_date:
                date = fields.Date.from_string(record.line_start_date)
                record.is_sunday = date.weekday() == 6  # Sunday is 6
            else:
                record.is_sunday = False

    @api.onchange('line_end_date', 'line_start_date', 'completed_date')
    def onchange_date_validation(self):
        if self.line_end_date and self.line_start_date:
            if self.line_end_date < self.line_start_date:
                raise ValidationError('Start date must be before End date')
        if self.completed_date and self.line_start_date:
            if self.completed_date < self.line_start_date:
                raise ValidationError('Completed date must be After Start date')

    @api.depends('line_end_date', 'line_start_date', 'is_done', 'done_date', 'completed_date')
    def compute_state(self):
        current_date = datetime.date.today()
        for rec in self:
            if rec.is_done:
                comparison_date = rec.line_end_date
                rec.state_1 = 'completed_g' if comparison_date and rec.done_date and comparison_date >= rec.done_date else 'completed_r'
            elif rec.line_start_date and rec.line_end_date:
                if rec.line_start_date > current_date:
                    rec.state_1 = 'open'
                else:
                    two_days_before_end_date = rec.line_end_date - datetime.timedelta(days=2)
                    if current_date >= two_days_before_end_date and current_date <= rec.line_end_date:
                        rec.state_1 = 'inprogress_o'
                    elif rec.line_end_date < current_date:
                        rec.state_1 = 'inprogress_r'
                    else:
                        rec.state_1 = 'inprogress_b'
            else:
                rec.state_1 = 'open' if not rec.line_start_date or rec.line_start_date > current_date else 'inprogress_b'

    def done_click(self):
        for rec in self:
            rec.state = 'completed'
            rec.is_done = True
            if rec.completed_date:
                rec.done_date = rec.completed_date
            else:
                rec.done_date = datetime.date.today()
            rec.compute_state()

    def reset_click(self):
        for rec in self:
            rec.state = 'pending'
            rec.is_done = False
            rec.compute_state()

    def refresh_click(self):
        for line in self:
            if line.state == 'completed':
                continue
            else:
                week_start = line.project_id.week_start
                line_start_date = line.line_start_date
                business_days_to_add = line.days
                while business_days_to_add > 0:
                    weekday = line_start_date.weekday()
                    line_start_date += datetime.timedelta(days=1)
                    if week_start == 'sunday' and weekday in [4, 5]:  # monday = 0, sunday = 6
                        continue
                    if week_start == 'monday' and weekday in [5, 6]:  # sunday = 6
                        continue
                    business_days_to_add -= 1

                line.line_end_date = line_start_date - datetime.timedelta(days=1)

    # @api.onchange('line_end_date')
    # def _onchange_line_end_date(self):
    #     for line in self:
    #         if line.state == 'completed':
    #             continue
    #         if line.line_start_date is not False and line.line_start_date is not False:
    #             week_start = line.project_id.week_start
    #             day_generator = (line.line_start_date + datetime.timedelta(x + 1) for x in
    #                              range((line.line_end_date - line.line_start_date).days))
    #             if week_start == 'sunday':
    #                 working_days = sum(1 for day in day_generator if day.weekday() not in [4, 5])
    #             if week_start == 'monday':
    #                 working_days = sum(1 for day in day_generator if day.weekday() not in [6, 5])
    #             self.days = working_days + 1
    @api.onchange('line_end_date')
    def _onchange_line_end_date(self):
        for line in self:
            if line.state == 'completed':
                continue
            if line.line_start_date and line.line_end_date:
                line.days = (line.line_end_date - line.line_start_date).days + 1
            else:
                line.days = 0

    new_seq = fields.Integer(default=1)

    def create_subsequence_call(self):
        if self.sequence:
            new_sub_seq = self.sequence + "." + str(self.new_seq)
            self.new_seq += 1
            self.project_id.create_subsequence_a(new_sub_seq)
        else:
            raise ValidationError(_("Create a sequnce"))
