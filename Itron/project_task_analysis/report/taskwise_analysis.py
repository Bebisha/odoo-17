from odoo import api,models, fields, tools,_
from datetime import date


class ResourseTaskStatus(models.Model):
    _name = 'res.task.status'
    _order = "stage desc"

    project_id = fields.Many2one('project.project', string='Project')
    milestone_id = fields.Many2one('project.milestone', string='Milestone')
    task_id = fields.Many2one('project.task')
    user_id = fields.Many2one('res.users')
    team_id = fields.Many2one('project.team')
    criticality = fields.Char()
    task_type = fields.Char()
    date_start = fields.Date(string='Start Date')
    date_deadline = fields.Date()
    open = fields.Integer()
    today = fields.Integer()
    over_due = fields.Integer()
    closed = fields.Integer()
    held = fields.Integer()
    fixed = fields.Integer()
    pending_tot = fields.Integer(string='Pending Total')
    total = fields.Integer()
    stage = fields.Selection([('Today','Today'),('Open','Open'),('Overdue','Overdue'),('Held','Held'),('Fixed','Fixed')],'Stage')


    def load_task_details(self):
        # Get the current logged-in user
        current_user = self.env.user
        print("current_user",current_user.name)
        # Check if the user is an admin (you can customize this based on your permissions model)
        admin = current_user.has_group('kg_itron_timesheet.group_project_administrator')
        is_admin = current_user.has_group('project.group_project_manager')


        teams = self.env['project.team'].search([])
        domain_list = []
        today = date.today()

        # If the user is not an admin, restrict the records to only tasks assigned to them
        if admin:
            # Filter teams to only include those where the current user is an employee
            teams = teams.filtered(lambda team: current_user not in team.employee_ids)
        elif is_admin:
            teams = teams.filtered(lambda team: current_user in team.timesheet_user_ids)


        # Loop through teams and employees
        for team in teams:
            for emp in team.employee_ids:
                # If not an admin, only load tasks for the logged-in user
                if not is_admin and emp.id != current_user.id:
                    continue

                emp_tasks = self.env['project.task'].search(
                    [('user_ids', '=', emp.id), ('stage_id.is_closed', '!=', True)])

                for task in emp_tasks:
                    stage = ''
                    open = 0
                    t_day = 0
                    over_due = 0
                    pending_tot = 0
                    fixed = 0
                    held = 0
                    total = 0
                    st = task.stage_id

                    # Check the task's status and classify it accordingly
                    if (st.is_open or st.is_progress) and task.date_deadline == today:
                        stage = 'Today'
                        t_day = 1
                    elif (st.is_open or st.is_progress) and task.date_deadline < today:
                        over_due = 1
                        stage = 'Overdue'
                    elif (st.is_open or st.is_progress) and task.date_deadline > today:
                        open = 1
                        stage = 'Open'
                    elif st.is_hold:
                        held = 1
                        stage = 'Held'
                    elif st.is_fixed:
                        fixed = 1
                        stage = 'Fixed'

                    if t_day == 1 or over_due == 1 or open == 1:
                        pending_tot = 1
                    if st.is_open or st.is_hold or st.is_fixed or st.is_progress:
                        total = 1

                    # Create a record for the task status
                    record = self.env['res.task.status'].create(
                        {'user_id': emp.id, 'team_id': team.id, 'project_id': task.project_id.id,
                         'open': open, 'today': t_day, 'over_due': over_due,
                         'held': held, 'total': total, 'pending_tot': pending_tot, 'fixed': fixed,
                         'task_id': task.id, 'task_type': task.task_type, 'date_start': task.date_start,
                         'date_deadline': task.date_deadline, 'criticality': task.criticality,
                         'milestone_id': task.milestone_ids.id, 'stage': stage}
                    )
                    domain_list.append(record.id)

                # If no tasks for the employee, create a placeholder record
                if not emp_tasks:
                    record = self.env['res.task.status'].create(
                        {'user_id': emp.id, 'team_id': team.id, 'project_id': False,
                         'open': 0, 'today': 0, 'over_due': 0,
                         'held': 0, 'total': 0, 'pending_tot': 0, 'fixed': 0,
                         'task_id': False, 'task_type': False, 'date_start': False,
                         'date_deadline': False, 'criticality': False,
                         'milestone_id': False, 'stage': False}
                    )
                    domain_list.append(record.id)

        # Include tasks that are not assigned to any employee (shown only to admins)
        if is_admin:
            emp_tasks = self.env['project.task'].search(
                [('user_ids', '=', False), ('stage_id.is_closed', '!=', True)])

            for task in emp_tasks:
                stage = ''
                open = 0
                t_day = 0
                over_due = 0
                pending_tot = 0
                fixed = 0
                held = 0
                total = 0
                st = task.stage_id

                if (st.is_open or st.is_progress) and task.date_deadline == today:
                    stage = 'Today'
                    t_day = 1
                elif (st.is_open or st.is_progress) and task.date_deadline < today:
                    over_due = 1
                    stage = 'Overdue'
                elif (st.is_open or st.is_progress) and task.date_deadline > today:
                    open = 1
                    stage = 'Open'
                elif st.is_hold:
                    held = 1
                    stage = 'Held'
                elif st.is_fixed:
                    fixed = 1
                    stage = 'Fixed'

                if t_day == 1 or over_due == 1 or open == 1:
                    pending_tot = 1
                if st.is_open or st.is_hold or st.is_fixed or st.is_progress:
                    total = 1

                # Create a record for the task status
                record = self.env['res.task.status'].create(
                    {'user_id': False, 'team_id': False, 'project_id': task.project_id.id,
                     'open': open, 'today': t_day, 'over_due': over_due,
                     'held': held, 'total': total, 'pending_tot': pending_tot, 'fixed': fixed,
                     'task_id': task.id, 'task_type': task.task_type, 'date_start': task.date_start,
                     'date_deadline': task.date_deadline, 'criticality': task.criticality,
                     'milestone_id': task.milestone_ids.id, 'stage': stage}
                )
                domain_list.append(record.id)

        return {
            'name': _('Task Report'),
            'view_type': 'form',
            'view_mode': 'pivot,tree',
            'domain': [('id', 'in', domain_list)],
            'context': {'search_default_groupby_team_id': 1, 'search_default_groupby_usr': 1, },
            'res_model': 'res.task.status',
            'type': 'ir.actions.act_window',
            'target': 'main'
        }
