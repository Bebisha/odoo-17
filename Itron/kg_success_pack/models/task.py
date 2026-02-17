# -*- coding: utf-8 -*-
from datetime import date

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class ProjectTask(models.Model):
    _inherit = "project.task"

    is_success_pack = fields.Boolean(related='project_id.active_success_pack')
    pack_project_id = fields.Many2one('pack.projects', string='Pack Project')
    success_pack_id = fields.Many2one('kg.success.pack', string='Success Pack')


    @api.constrains('allocated_hours')
    def _onchange_allocated_hours(self):
        if self.pack_project_id:
            tasks = self.env['project.task'].search([('pack_project_id', '=', self.pack_project_id.id)])
            print(tasks)

            total_allocated = sum(tasks.mapped('allocated_hours') or [0.0])

            if total_allocated > self.pack_project_id.estimated_hours:
                raise ValidationError(
                    f"Total allocated hours ({total_allocated}) exceed the planned hours "
                    f"({self.pack_project_id.estimated_hours}) for the selected project."
                )



    @api.onchange('pack_project_id', 'partner_id')
    def _onchange_partner_id(self):
        """ onchange pack_project_id and partner_id to pass the values """
        self.partner_id = self.pack_project_id.partner_id.id
        if self.partner_id:
            pack_lines = self.env['sale.order'].sudo().search([
                ('partner_id', '=', self.partner_id.id), ('pack_project_id', '=', self.pack_project_id.id)
            ])
            for pac in pack_lines:
                self.success_pack_id = pac.success_pack_id.id
                self.date_start = pac.start_date

        #     valid_pack_lines = [line for line in pack_lines if line.remaining_hours > 0]
        #
        #     return {
        #         'domain': {
        #             'success_pack_id': [('id', 'in', list(set(line.success_pack_id.id for line in valid_pack_lines)))]
        #         }
        #     }
        #
        # return {
        #     'domain': {
        #         'success_pack_id': []
        #     }
        # }

    @api.constrains('date_start', 'success_pack_id')
    def validation_error(self):
        """ set validation error for date"""
        self.partner_id = self.pack_project_id.partner_id.id
        if self.partner_id:
            pack_lines = self.env['sale.order'].sudo().search([

                ('partner_id', '=', self.partner_id.id), ('pack_project_id', '=', self.pack_project_id.id)
            ])
            for pack in pack_lines:
                if self.date_start and pack.start_date and self.date_start < pack.start_date:
                    raise ValidationError("Start date cannot be earlier than the selected pack's start date")
                # if self.success_pack_id != pack.success_pack_id:
                #     raise ValidationError('The selected Success Pack is not active for this selected project')
                if pack.remaining_hours <= 0 or self.allocated_hours > pack.remaining_hours:
                    raise ValidationError(
                        'Allocated hours exceed the available remaining hours in the selected Success Pack.')

class HrTimesheet(models.Model):
    _inherit = "account.analytic.line"

    success_pack_id = fields.Many2one(related='task_id.success_pack_id')
    pack_project_id = fields.Many2one('pack.projects',related='task_id.pack_project_id')


    def format_hours(self, hours_float):
        hours_int = int(hours_float)
        minutes = int(round((hours_float - hours_int) * 60))
        return f"{hours_int:02d}:{minutes:02d}"

    @api.model_create_multi
    def create(self, vals_list):
        res = super(HrTimesheet, self).create(vals_list)
        for rec in self:
            if rec.task_id.success_pack_id:
                timesheets = self.env['account.analytic.line'].sudo().search([('project_id.partner_id', '=',
                                                                               rec.project_id.partner_id.id),
                                                                              ('id', '!=', rec.id),
                                                                              ('task_id.success_pack_id', '=',
                                                                               rec.task_id.success_pack_id.id)])
                spent_hours = sum(timesheets.mapped('unit_amount'))
                total_spent_hours = spent_hours + rec.unit_amount
                max_pack_hours = rec.task_id.success_pack_id.hours
                if total_spent_hours > (max_pack_hours + 8):
                    remaining_hours = max_pack_hours + 8 - spent_hours
                    if spent_hours > max_pack_hours:
                        remaining_hours = 0
                    raise ValidationError(
                        _('The success pack’s %s allocated hours are nearly exhausted, with only about %s hours remaining.' % (
                        self.format_hours(max_pack_hours), self.format_hours(remaining_hours))))
        return res

    def write(self, values):
        res = super(HrTimesheet, self).write(values)
        for rec in self:
            if rec.task_id.success_pack_id:
                timesheets = self.env['account.analytic.line'].sudo().search([('project_id.partner_id', '=',
                                                                               rec.project_id.partner_id.id),
                                                                              ('id', '!=', rec.id),
                                                                              ('task_id.success_pack_id', '=',
                                                                                  rec.task_id.success_pack_id.id)])
                spent_hours = sum(timesheets.mapped('unit_amount'))
                total_spent_hours = spent_hours + rec.unit_amount
                max_pack_hours = rec.task_id.success_pack_id.hours
                if total_spent_hours > (max_pack_hours + 8):
                    remaining_hours = max_pack_hours + 8 - spent_hours
                    if spent_hours > max_pack_hours:
                        remaining_hours = 0
                    raise ValidationError(_('The success pack’s %s allocated hours are nearly exhausted, with only about %s hours remaining.'%(self.format_hours(max_pack_hours), self.format_hours(remaining_hours))))
        return res