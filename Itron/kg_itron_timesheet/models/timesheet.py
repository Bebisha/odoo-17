# -*- coding: utf-8 -*-
import ast

from odoo import models, fields, api
import datetime 
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class KgTimesheet(models.Model):
	_inherit = 'account.analytic.line'

	date_start = fields.Datetime()
	date_end = fields.Datetime()
	project_activity = fields.Selection([
		('project', 'Project'),
		('activity', 'Activity'),
		('success_pack', 'Success Pack'),
	], 'Project/Activity', default='',)
	activity_id = fields.Many2one('mail.activity', string="Activity Name",domain="[ ('res_model', '=', 'custom.activity')]",)
	activities_id = fields.Many2one('custom.activity')
	activity_name = fields.Char(related="activity_id.summary", string="Activity Name")
	milestone_id = fields.Many2one(related='task_id.milestone_ids')

	@api.onchange('project_activity')
	def _onchange_project_activity(self):
		print("self.project_activity",self.project_activity)
		if self.project_activity == 'activity':
			self.project_id = self.env['project.project'].search([('name', '=', 'Activity')], limit=1)
		elif self.project_activity == 'success_pack':
			self.project_id = self.env['project.project'].sudo().search([('name', '=', 'Success Pack Projects')], limit=1)
		else:
			self.project_id = False

	@api.model
	def create(self, vals):
		if vals.get('project_activity') == 'activity':
			project = self.env['project.project'].search([('name', '=', 'Activity')], limit=1)
			vals['project_id'] = project.id if project else False

		elif vals.get('project_activity') == 'success_pack':
			project = self.env['project.project'].search([('name', '=', 'Success Pack Project')], limit=1)
			vals['project_id'] = project.id if project else False
		return super(KgTimesheet, self).create(vals)

	def write(self, vals):
		if vals.get('project_activity') == 'activity':
			project = self.env['project.project'].search([('name', '=', 'Activity')], limit=1)
			vals['project_id'] = project.id if project else False
		elif vals.get('project_activity') == 'success_pack':
			project = self.env['project.project'].search([('name', '=', 'Success Pack Project')], limit=1)
			vals['project_id'] = project.id if project else False
		return super(KgTimesheet, self).write(vals)
	# test = fields.Float()

	@api.onchange('date_start','date_end','project_id','task_id')
	def get_hourse_minute(self):
		if self.task_id and self.date:
			task_start = self.task_id.date_start
			task_end = self.task_id.date_deadline


			if task_start and self.date_start and self.date_start.date() < task_start:
				raise ValidationError("The selected date is before the task's start date.")

			# if self.project_activity == 'success_pack' and task_end and self.date_end and self.date_end.date() > task_end:
			# 	raise ValidationError("The selected date is after the task's end date .")

		if self.date_start and self.date_end:
			delta = self.date_end - self.date_start
			if self.date_end == self.date_start:
				raise ValidationError('The start date and end date must not be the same.')
			if self.date_end < self.date_start:
				raise ValidationError('Start time should be less than end time.')
			self.unit_amount = delta.total_seconds() / 3600.0
			if self.date_end.date() != self.date_start.date():
				raise ValidationError("The Start date and End date should be on the same day ")

	# def missing_timesheet(self):
	# 	user = self.env.user
	# 	is_admin = user.has_group('base.group_system')
	#
	# 	teams = self.env['project.team'].sudo().search([('timesheet_user_ids', '=', user.id)])
	# 	print("teams:", teams)
	#
	# 	last_working_date = datetime.date.today() - datetime.timedelta(days=1)
	# 	user_company_id = self.env.company.id
	# 	print('self.env.company.country_code', self.env.company.country_code, datetime.date.today().strftime("%A"))
	# 	if self.env.company.country_code in ['IN', "AE"] and datetime.date.today().strftime("%A") == 'Monday':
	# 		last_working_date = datetime.date.today() - datetime.timedelta(days=3)
	# 	elif self.env.company.country_code not in ['IN', "AE"] and datetime.date.today().strftime("%A") == 'Sunday':
	# 		last_working_date = datetime.date.today() - datetime.timedelta(days=3)
	#
	# 	domain = [
	# 		('date_start', '<=', last_working_date),
	# 		('date_end', '>=', last_working_date),
	# 	]
	#
	# 	team_member_ids = []
	#
	# 	if not is_admin and teams:
	# 		user_ids = teams.mapped('employee_ids').ids
	# 		print("team_member_ids:", teams.mapped('employee_ids'))
	# 		employees = self.env['hr.employee'].sudo().search(
	# 			[('user_id', 'in', user_ids), ('company_id', '=', user_company_id)])
	# 		team_member_ids = employees.ids
	# 	elif not is_admin and not teams:
	# 		print("team_member_idswqwq:", teams.mapped('employee_ids'))
	# 		employees = self.env['hr.employee'].sudo().search(
	# 			[('user_id', '=', user.id), ('company_id', '=', user_company_id)])
	# 		team_member_ids = employees.ids
	# 	else:
	# 		employees = self.env['hr.employee'].sudo().search([('company_id', '=', user_company_id)])
	# 		team_member_ids = employees.ids
	# 	print("final_domain:", domain)
	#
	# 	if team_member_ids:
	# 		domain.append(('employee_id', 'in', team_member_ids))
	#
	# 	missing_timesheets = []
	#
	# 	timesheets = self.env['account.analytic.line'].sudo().search(domain)
	# 	print(timesheets, "rrrrrrrr")
	#
	# 	timesheet_dict = {}
	# 	for ts in timesheets:
	# 		if ts.employee_id.id not in timesheet_dict:
	# 			timesheet_dict[ts.employee_id.id] = self.env['account.analytic.line']
	# 		timesheet_dict[ts.employee_id.id] |= ts
	#
	# 	for employee in employees:
	# 		company_employee_data = {
	# 			'id': employee.id,
	# 			'name': employee.name,
	# 			'timesheet_submitted': False,
	# 			'hour_spent': "00:00",
	# 			'timesheets': []
	# 		}
	# 		missing_timesheets.append(company_employee_data)
	#
	# 		calendar = employee.resource_calendar_id
	# 		if not calendar:
	# 			continue
	#
	# 		unique_sorted_list = sorted(set(calendar.attendance_ids.mapped('dayofweek')))
	# 		closest_day = None
	# 		closest_date = None
	# 		today = datetime.date.today()
	#
	# 		for day in unique_sorted_list:
	# 			current_day = today.weekday()
	# 			day = int(day)
	# 			if current_day > day:
	# 				delta_days = current_day - day
	# 				target_date = today - datetime.timedelta(days=delta_days)
	# 				if closest_date is None or target_date > closest_date:
	# 					closest_day = day
	# 					closest_date = target_date
	# 					print("closest_date", closest_date)
	# 			elif current_day < day:
	# 				delta_days = current_day - day + 7
	# 				target_date = today - datetime.timedelta(days=delta_days)
	# 				if closest_date is None or target_date > closest_date:
	# 					closest_day = day
	# 					closest_date = target_date
	#
	# 		# if closest_date == yesterday:
	# 		if employee.id in timesheet_dict:
	# 			timesheets_for_employee = timesheet_dict[employee.id]
	# 			total_hours = sum(timesheets_for_employee.mapped('unit_amount'))
	# 			hours = int(total_hours)
	# 			minutes = int((total_hours - hours) * 60)
	# 			formatted_hours = f"{hours:02}:{minutes:02}"
	#
	# 			if 0 < total_hours < 8:
	# 				company_employee_data['timesheet_submitted'] = True
	# 				company_employee_data['hour_spent'] = formatted_hours
	# 				company_employee_data['timesheets'] = timesheets_for_employee.ids
	# 			elif total_hours >= 8:
	# 				missing_timesheets.remove(company_employee_data)
	# 		else:
	# 			company_employee_data['timesheet_submitted'] = False
	# 			company_employee_data['hour_spent'] = "00:00"
	#
	# 	return missing_timesheets