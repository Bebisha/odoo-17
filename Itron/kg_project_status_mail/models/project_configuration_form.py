# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)


class ProjectStatus(models.Model):
    _name = 'project.status.config'
    _description = 'Configuring users and project'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'company_id'

    user_ids = fields.Many2many('res.users')
    project_ids = fields.Many2many('project.project')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    project_team_id = fields.Many2one('project.team', string='Project Team')

    def get_mail_template(self):

        """Scheduler calling the mail template"""
        try:
            for conf in self.env['project.status.config'].search([]):
                email_values = {'email_to': ",".join([u.login for u in conf.user_ids]) or ''}
                mail_template = conf.env.ref("kg_project_status_mail.project_status_mail_template")
                mail_template.send_mail(conf.id, email_values=email_values, force_send=True)
        except Exception as e:
            _logger.info("Project Mail error : ", str(e))

    def get_user_email_dtls(self):
        """Getting user mail list from configuration"""
        # config = self.env['project.status.config'].search([],limit=1)
        # users_list = []
        # for con in config:
        # 	for user in con.user_ids:
        # 		users_list.append(user.login)
        users_list = [u.login for u in self.user_ids]
        mail_list = ",".join(users_list)
        return mail_list

    # getting project task details
    def get_project_dtls(self):
        task_list = []
        si = 1
        # config = self.env['project.status.config'].search([],limit=1)
        config = self
        if len(config) > 0:
            closed_stages = self.env['project.task.type'].search([('is_closed', '=', True)])
            for task in self.env['project.task'].search(
                    [('project_id', 'in', config.project_ids.ids), ('active', '=', True),
                     ('stage_id', 'not in', closed_stages.ids)
                     ]):
                task_list.append({'si': si,
                                  'resource': task.user_ids[0].partner_id.name if len(task.user_ids) > 0 else "",
                                  'project': task.project_id.name,
                                  'task': task.name,
                                  'dead_line': task.date_deadline if task.date_deadline else ""})
                si += 1
        return task_list

    # getting timesheet details
    def get_time_sheet_dtls(self):
        sheet_list = []
        si = 1
        # config = self.env['project.status.config'].search([],limit=1)
        config = self
        if len(config) > 0:
            for sheet in self.env['account.analytic.line'].search(
                    [('project_id', 'in', config.project_ids.ids), ('date', '=', (date.today() - timedelta(days=1)))]):
                sheet_list.append({'si': si,
                                   'resource': sheet.task_id.user_ids[0].partner_id.name if len(
                                       sheet.task_id.user_ids) > 0 else "",
                                   'project': sheet.project_id.name,
                                   'task': sheet.task_id.name,
                                   'description': sheet.name,
                                   'duration': sheet.unit_amount, })
                si += 1
        return sheet_list

    # getting timesheet details
    def get_merged_time_sheet_dtls(self):
        si = 1
        resrcs_dict = {}
        # config = self.env['project.status.config'].search([],limit=1)
        config = self
        if len(config) > 0:
            sheets = self.env['account.analytic.line'].search(
                [('project_id', 'in', config.project_ids.ids), ('date', '=', (date.today() - timedelta(days=1)))])
            resources = list(sheets.task_id.user_ids.partner_id)
            for resrcs in resources:
                resrcs_dict[resrcs] = {'resource_name': resrcs.name if len(
                    sheets.task_id.user_ids) > 0 else "",
                                       'sl_no': si,
                                       'row_count': 0,
                                       'details': {}}
                si += 1
            for resrcs in resources:
                sheet_list = []
                for sheet in sheets:
                    if resrcs == sheet.task_id.user_ids.partner_id:
                        sheet_list.append({'project': sheet.project_id.name,
                                           'task': sheet.task_id.name,
                                           'description': sheet.name,
                                           'duration': sheet.unit_amount, })
                        resrcs_dict[resrcs]['details'] = sheet_list
                        resrcs_dict[resrcs]['row_count'] = resrcs_dict[resrcs]['row_count'] + 1
        return resrcs_dict

    # getting project task details
    def get_merged_project_task_status(self):
        si = 1
        proj_dict = {}
        config = self
        if len(config) > 0:
            closed_stages = self.env['project.task.type'].search([('is_closed', '=', True)])
            tasks = self.env['project.task'].search(
                [('project_id', 'in', config.project_ids.ids), ('active', '=', True),
                 ('stage_id', 'not in', closed_stages.ids)
                 ])
            projects = list(tasks.mapped('project_id'))
            for proj in projects:
                proj_dict[proj] = {'project_name': proj.name, 'sl_no': si, 'row_count': 0, 'details': {}}
                si += 1
            for proj in projects:
                task_list = []
                for task in tasks:
                    if proj == task.project_id:
                        task_list.append({
                            'resource': task.user_ids[0].partner_id.name if len(task.user_ids) > 0 else "",
                            'task': task.name,
                            'dead_line': task.date_deadline if task.date_deadline else ""})
                        proj_dict[proj]['details'] = task_list
                        proj_dict[proj]['row_count'] = proj_dict[proj]['row_count'] + 1
        return proj_dict

    def action_send_project_details(self):
        for conf in self.search([]):
            users_list = [u.login for u in conf.user_ids]
            mail_list = ",".join(users_list)
            email_values = {
                'email_to': mail_list,
                # 'email_from': self.env.user.email_formatted,
            }
            mail_template = self.env.ref('kg_project_status_mail.project_detail_email_template')
            mail_template.send_mail(conf.id, force_send=True, email_values=email_values)
