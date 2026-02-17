from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class KGProjectStatusWizard(models.TransientModel):
    """Project Status Update wizard."""

    _name = 'project.status.update.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    project = fields.Many2many('project.project', string='Project')

    def button_project_updates_report(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))

        vals = []
        if not self.project:
            projects = self.env['project.project'].search([])
            for pro in projects:
                project = {'type': 'project',
                           'project_name': pro.name,
                           'lines': []
                           }
                project_id = self.env['project.update'].search(
                    [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('project_id', '=', pro.id)],
                    order='date desc')
                for data in project_id:
                    update = data.name
                    date = data.date
                    status = dict(data.fields_get(allfields=['status'])['status']['selection'])[data.status]
                    detailed_update = data.description
                    project_vals = {'type': 'project_data',
                                    'update': update,
                                    'date': date,
                                    'status': status,
                                    'detailed_update': detailed_update,
                                    }
                    project['lines'].append(project_vals)
                if project['lines']:
                    vals.append(project)
        if self.project:
            projects = self.env['project.project'].search([])
            for pro in projects:
                project = {'type': 'project',
                           'project_name': pro.name,
                           'lines': []
                           }
                project_id = self.env['project.update'].search(
                    [('date', '>=', self.date_from), ('date', '<=', self.date_to),
                     ('project_id', 'in', self.project.ids), ('project_id', '=', pro.id)],
                    order='date desc')
                for data in project_id:
                    update = data.name
                    date = data.date
                    status = dict(data.fields_get(allfields=['status'])['status']['selection'])[data.status]
                    detailed_update = data.description
                    project_vals = {'type': 'project_data',
                                    'update': update,
                                    'date': date,
                                    'status': status,
                                    'detailed_update': detailed_update,
                                    }
                    project['lines'].append(project_vals)
                if project['lines']:
                    vals.append(project)

        if not vals:
            raise UserError(_('No Data In This Date Range'))

        data = {
            'form_data': self.read()[0],
            'values': vals,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'project': self.project,
        }
        return self.env.ref('kg_project_milestone.action_project_updates_report').report_action(self, data=data)

    def button_project_updates_report_view(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))

        vals = []
        if not self.project:
            projects = self.env['project.project'].search([])
            for pro in projects:
                project = {'type': 'project',
                           'project_name': pro.name,
                           'lines': []
                           }
                project_id = self.env['project.update'].search(
                    [('date', '>=', self.date_from), ('date', '<=', self.date_to), ('project_id', '=', pro.id)],
                    order='date desc')
                for data in project_id:
                    update = data.name
                    date = data.date
                    status = dict(data.fields_get(allfields=['status'])['status']['selection'])[data.status]
                    detailed_update = data.description
                    project_vals = {'type': 'project_data',
                                    'update': update,
                                    'date': date,
                                    'status': status,
                                    'detailed_update': detailed_update,
                                    }
                    project['lines'].append(project_vals)
                if project['lines']:
                    vals.append(project)
        if self.project:
            projects = self.env['project.project'].search([])
            for pro in projects:
                project = {'type': 'project',
                           'project_name': pro.name,
                           'lines': []
                           }
                project_id = self.env['project.update'].search(
                    [('date', '>=', self.date_from), ('date', '<=', self.date_to),
                     ('project_id', 'in', self.project.ids), ('project_id', '=', pro.id)],
                    order='date desc')
                for data in project_id:
                    update = data.name
                    date = data.date
                    status = dict(data.fields_get(allfields=['status'])['status']['selection'])[data.status]
                    detailed_update = data.description
                    project_vals = {'type': 'project_data',
                                    'update': update,
                                    'date': date,
                                    'status': status,
                                    'detailed_update': detailed_update,
                                    }
                    project['lines'].append(project_vals)
                if project['lines']:
                    vals.append(project)

        if not vals:
            raise UserError(_('No Data In This Date Range'))

        data = {
            'form_data': self.read()[0],
            'values': vals,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'project': self.project,
        }
        return self.env.ref('kg_project_milestone.action_project_updates_report_html').report_action(self, data=data)
