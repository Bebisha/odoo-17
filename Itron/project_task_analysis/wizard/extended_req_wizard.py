# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, tools, _, api, Command
from odoo.exceptions import ValidationError


class ProjectContractRequestExtend(models.Model):
    _name = 'extended.resource'

    is_new = fields.Boolean(string='New Task', default=True, readonly=False)
    # is_exist = fields.Boolean('Existing Task')
    resource_id = fields.Many2one('project.resource.pool')
    extend_hrs = fields.Float('Extended Hours', compute='compute_extd_hrs', store=True)
    extend_date = fields.Date('Extend Date', required=True)
    # extd_dead_line = fields.Date('Extended Date')
    comments = fields.Html('Extension Reason', required=True)

    task_ids = fields.One2many('extended.resource.line', 'extended_id', string='Task Lines')

    # @api.onchange('extend_date')
    # def onchange_date(self):
    #     if self.extend_date < self.resource_id.date_end:
    #         raise ValidationError('Extend Date is less than End date !!')

    @api.depends('task_ids')
    def compute_extd_hrs(self):
        for value in self:
            planned_hrs = sum(rec.planned_hrs for rec in value.task_ids)
            if not value.is_new:
                planned_hrs = sum(rec.extend_hrs for rec in value.task_ids)
            value.write({'extend_hrs': planned_hrs})

    @api.onchange('is_new')
    def onchange_bool_(self):
        self.task_ids = False
        if not self.is_new:
            linked_tasks = []
            for task_id in self.resource_id.task_ids:
                linked_tasks.append((0, 0, {
                    'line': task_id.id,
                    'description': task_id.description,
                    'start_date': task_id.start_date,
                    'end_date': task_id.end_date,
                    'planned_hrs': task_id.planned_hrs,
                    'task_id': task_id.task_id.id

                }))

            self.write({'task_ids': linked_tasks})

    def confirm_button(self):
        """Confirm button"""
        if self.is_new:
            linked_lines = [(0, 0, {
                'description': rec.description,
                'start_date': rec.start_date,
                'end_date': rec.end_date,
                'planned_hrs': rec.planned_hrs,
                'ext_bool': True,
                # 'extend_hrs':rec.extend_hrs,
            }) for rec in self.task_ids]
            self.resource_id.write({'task_ids': linked_lines,})

        else:
            for rec in self.task_ids:
                rec.line.write({
                    'planned_hrs': rec.planned_hrs + rec.extend_hrs,
                    'end_date': rec.end_date ,
                    'extend_hrs': rec.extend_hrs
                })
        if self.extend_date:
            self.resource_id.date_end = self.extend_date
        self.resource_id.write(({
            'state': 'send',
            'extend_':True
        }))
        self.resource_id.extend_count += 1
        self.send_mail_()

    def hour_format(self, hrs):
        hours = int(hrs)
        minutes = int((hrs - hours) * 60)
        formatted_hrs = f"{hours}:{minutes:02d}"
        return formatted_hrs

    def send_mail_(self):
        """Send email to approvers"""
        approval_ids = self.env['ir.config_parameter'].sudo().get_param('project_task_analysis.approval_ids')
        group_send_mail = []
        for config_rec in self.env['res.users'].browse(eval(approval_ids)):
            if config_rec.email:
                group_send_mail.append(config_rec.email)

        project_name = self.resource_id.project_id.name
        subject = _('Resource Extension Request for the Project "%s"') % project_name

        task_names = str(
            ["<li>" + task.description + " - " + str(self.hour_format(task.extend_hrs)) + " hrs " + "</li>" for task in self.task_ids])
        cleaned_string = task_names.replace("[", "").replace("]", "").replace("', '", "").replace("'", "")
        user_names = [user.name for user in self.resource_id.user_ids]
        task_names_list = cleaned_string
        users_list = ", ".join(user_names)

        body = _('''
            <p>Hi Sir/Madam,</p>
            <p>I hope this message finds you well.</p>
            <p>An extension request has been submitted for the project "<strong>%s</strong>" by <strong>%s</strong>. Here are the details:</p>
            <p><strong>Date: </strong>From %s to %s</p>
            <p><strong>Resource: </strong>%s</p>
            <p><strong>Extended Hours: </strong>%s hrs</p>
            <p><strong>Reasons for Extension: </strong>%s</p>
            <p><strong>Extended Tasks: </strong><br/><ul>%s</ul></p>
            <p>%s</p>
            Please review the details and take the necessary action by clicking on one of the options below:<br>
            Thank you for your attention to this matter.<br>
            <br>
        ''') % (
            self.resource_id.project_id.name,
            self.resource_id.users_id.name,
            str(self.resource_id.date_start),
            str(self.resource_id.date_end),
            users_list,
            self.hour_format(self.extend_hrs),
            self.comments,
            task_names_list,
            self.resource_id.description if self.resource_id.description else ''
        )

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        button_url = "{}/project_task_analysis/approve_task?record_id={}".format(base_url, self.resource_id.id)
        reject_url = "{}/web#id={}&view_type=form&model={}".format(base_url, self.resource_id.id,
                                                                   self.resource_id._name)

        html_content = """

            <a href="{}">
                <button style='background-color: #71639e;color:white;height:35px;border-radius:10px;'>
                    VIEW REQUEST
                </button>
            </a>
        """.format(button_url, reject_url)

        mail_values = {
            'subject': subject,
            'body_html': body + "<br/>" + html_content,
            'email_to': ', '.join(group_send_mail),
        }

        # Send the email
        self.env['mail.mail'].create(mail_values).send()

    class ProjectContractRequestExtendLine(models.Model):
        _name = 'extended.resource.line'

        description = fields.Char('Task Description', store=True)
        line = fields.Many2one('resource.task.line', store=True)
        start_date = fields.Date('Start Date', default=fields.Date.context_today)
        end_date = fields.Date('End Date')
        planned_hrs = fields.Float('Planned hours')
        extend_hrs = fields.Float('Extra Hrs')
        extended_id = fields.Many2one('extended.resource')
        task_id = fields.Many2one('project.task')

        @api.onchange('end_date')
        def validation_date(self):
            if self.end_date and self.start_date:
                if self.end_date < self.start_date:
                    raise ValidationError('End date is less than Start date')
                if self.end_date > self.extended_id.extend_date:
                    raise ValidationError('End date is greater than Allocation date')
