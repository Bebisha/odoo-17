# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError,UserError


class Kg_Product(models.Model):
	_inherit = 'project.task'

	date_deadline = fields.Date(string='Deadline',default=fields.Date.today(), index=True, copy=False, tracking=True, task_dependency_tracking=True,required=True)

	company_id = fields.Many2one('res.company', string='Company', compute='_compute_company_id', store=True,
								 readonly=False, recursive=True, copy=True, default=lambda self: self.env.company,)

	@api.depends('project_id.company_id', 'parent_id.company_id')
	def _compute_company_id(self):
		for task in self:
			task.company_id = self.env.company.id

	def unlink(self):
		for task in self:
			user = self.env.user
			if user.has_group('project.group_project_user') and not user.has_group('project.group_project_manager'):
				raise UserError(_('You do not have permission to delete tasks.'))
		return super(Kg_Product, self).unlink()
