# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from bs4 import BeautifulSoup


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    project_id = fields.Many2one('project.project', string='Project', copy=False)
    task_ids = fields.Many2many('project.task', string='Task', copy=False, readonly=True, strore=True)
    tasks_ids = fields.One2many('project.task', 'ticket_id', string='Task', copy=False, readonly=True, strore=True)
    task_count = fields.Integer(string='Task Count', readonly=True, copy=False, compute='compute_task_count')
    hours_spent = fields.Float(string='Hours Spent')
    allocated_hours = fields.Float(string='Allocated Hours')
    milestone_id = fields.Many2one('project.milestone', string='Milestone')
    task_start_date = fields.Date(string='Task Start Date')
    task_deadline = fields.Date(string='Task Deadline')
    task_tags = fields.Many2many('project.tags', string='Task Tags')
    activity_count = fields.Integer(string='Activity Count', readonly=True, copy=False,
                                    compute='compute_activity_count')
    pack_project_id = fields.Many2one('pack.projects', string='Pack Project' )


    @api.constrains('stage_id')
    def onchange_stage_id(self):
        """ UserError for Hours Spent for Odoo Team """
        for ticket in self:
            if ticket.closed:
                if ticket.hours_spent == 0.0 and ticket.team_id.is_odoo:
                    raise UserError("Please Enter Hours Spent!")

    def action_create_task(self):
        """ Create Task from ticket """
        for rec in self:
            if not rec.project_id or not rec.user_id:
                raise ValidationError(_('Either a project or an assignee is mandatory to proceed.'))
            if not rec.allocated_hours:
                raise ValidationError("Please enter allocated hours for creation of task")
            task = self.env['project.task'].sudo().create({
                'name': rec.name,
                'project_id': rec.project_id.id,
                'ticket_id': rec.id,
                'date_start': date.today(),
                'task_type': 'bug',
                'company_id': rec.user_id.company_id.id,
                'allocated_hours': rec.allocated_hours,
                'user_ids': [fields.Command.link(rec.user_id.id)] if rec.user_id else [],
                'tag_ids': [fields.Command.link(rec.task_tags.id)] if rec.task_tags else [],
                'description': rec.description,
                'pack_project_id': rec.pack_project_id.id,
                'success_pack_id': rec.pack_project_id.success_pack_id.id,
                'partner_id': rec.pack_project_id.partner_id.id,
            })
            self.env['ir.attachment'].sudo().create([
                {
                    'name': attachment.name,
                    'type': 'binary',
                    'datas': attachment.datas,
                    'res_model': 'project.task',
                    'res_id': task.id,
                    'mimetype': attachment.mimetype,
                }
                for attachment in rec.attachment_ids
            ])
            stage = rec.env['helpdesk.ticket.stage'].search(
                [('in_progress', '=', True)], limit=1)
            rec.write({'tasks_ids': [fields.Command.link(task.id)],
                       'stage_id': stage.id})
        return {'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'view_mode': 'form',
                'res_id': task.id,
                'target': 'current',
                }

    def action_open_task(self):
        """ Smart button to display created tasks. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Task's",
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            'context': "{'create':False}",
            'domain': [('id', 'in', self.tasks_ids.ids)]
        }

    def action_open_activity(self):
        """ Smart button to display created activity. """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Activities",
            'view_mode': 'tree,form',
            'res_model': 'mail.activity',
            'context': "{'create':False}",
            'domain': [('id', 'in', self.activity_ids.ids)]
        }

    def compute_task_count(self):
        """ Compute task count in smart tab """
        for rec in self:
            rec.task_count = len(rec.tasks_ids) if rec.tasks_ids else 0

    def compute_activity_count(self):
        """ Compute activity count in smart tab """
        for rec in self:
            rec.activity_count = len(rec.activity_ids) if rec.activity_ids else 0

    def compute_task_hrs(self):
        """Compute the worked hours for the task."""
        for rec in self:
            rec.hours_spent = sum(rec.tasks_ids.mapped('effective_hours')) if rec.tasks_ids else 0

    def action_create_activity(self):
        """ button to create activity """
        if not self.user_id:
            raise ValidationError('Please choose an assignee before creating the activity.')
        plain_description = BeautifulSoup(self.description or '', 'html.parser').get_text()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Activity',
            'view_mode': 'form',
            'res_model': 'mail.activity.schedule',
            'context': {'default_helpdesk_id': self.id,
                        'default_summary': self.name,
                        'default_note': plain_description,
                        'default_activity_user_id': self.user_id.id,
                        'from_helpdesk_button': True,
                        },
            'target': 'new'
        }

    @api.onchange('stage_id')
    def _onchange_stage_id(self):
        """ onchange stage to set the validation """
        for helpdesk in self:
            if helpdesk.stage_id and helpdesk.stage_id.closed:
                incomplete_tasks = helpdesk.tasks_ids.filtered(lambda task: not task.stage_id.is_closed)
                if incomplete_tasks:
                    raise ValidationError('You cannot close the ticket, if Tasks are not done.')
                incomplete_activities = helpdesk.activity_ids.filtered(lambda a: a.stage != 'completed')
                if incomplete_activities:
                    raise ValidationError('You cannot close the ticket if activities are not completed.')


class HelpdeskTicketStages(models.Model):
    _inherit = "helpdesk.ticket.stage"

    in_progress = fields.Boolean(string='In Progress', default=False, copy=False)


class HelpdeskTicketTeam(models.Model):
    _inherit = "helpdesk.ticket.team"

    is_odoo = fields.Boolean(string='Odoo Team', copy=False)
