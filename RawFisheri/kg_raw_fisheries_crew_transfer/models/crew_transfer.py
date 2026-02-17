# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class CrewTransfer(models.Model):
    _name = 'crew.transfer'
    _description = 'crew.transfer'

    crew_transfer_line_ids = fields.One2many('crew.transfer.line', 'crew_transfer_id', string='Crew Transfer')
    name = fields.Char(string='Reference', default=lambda self: _('New'), readonly=True)
    old_vessel_id = fields.Many2one('sponsor.sponsor', string='Old Vessel', required=True)
    new_vessel_id = fields.Many2one('sponsor.sponsor', string='New Vessel', required=True)
    state = fields.Selection([('draft', "Draft"), ('transfer', "Transferred")], string="State", default='draft')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    date_transfer = fields.Date(string='Transfer Date', reqired=True)

    @api.model
    def create(self, vals):
        """ Crew Transfer sequence number generation """
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'crew.transfer.sequence') or _('New')
        return super(CrewTransfer, self).create(vals)

    # @api.onchange('old_vessel_id')
    # def onchange_old_vessel_id(self):
    #     """ Listing the crew members on the basis of old vessel """
    #     for crew in self:
    #         if crew.old_vessel_id:
    #             employees = self.env['hr.employee'].search([('sponsor_name', '=', crew.old_vessel_id.id)])
    #             crew.crew_transfer_line_ids = [(5, 0, 0)]
    #             crew.crew_transfer_line_ids = [(0, 0, {
    #                 'employee_id': employee.id,
    #             }) for employee in employees]

    def action_transfer(self):
        """ Function to transfer the crew from one vessel to another """
        for crew in self:
            if crew.old_vessel_id == crew.new_vessel_id:
                raise UserError("You cannot perform transfer between the same vessels")
            if not crew.new_vessel_id:
                raise UserError("Please add a new vessel for the transfer!")
            for lines in crew.crew_transfer_line_ids:
                lines.employee_id.write({
                    'sponsor_name': crew.new_vessel_id.id
                })
                lines.employee_id.contract_id.write({
                    'state': 'close',
                    'date_end': crew.date_transfer - timedelta(days=1),
                })
                vals = {
                    'name': lines.employee_id.contract_id.name,
                    'state': 'open',
                    'employee_id': lines.employee_id.id,
                    'date_start': crew.date_transfer,
                    # 'date_end': lines.employee_id.contract_id.date_end,
                    'wage': lines.employee_id.contract_id.wage,
                    'housing_allowance': lines.employee_id.contract_id.housing_allowance if lines.employee_id.contract_id.housing_allowance else 0.0,
                    'travel_allowance': lines.employee_id.contract_id.travel_allowance if lines.employee_id.contract_id.travel_allowance else 0.0,
                    'other_allowance': lines.employee_id.contract_id.other_allowance if lines.employee_id.contract_id.other_allowance else 0.0,
                    'extra_income': lines.employee_id.contract_id.extra_income if lines.employee_id.contract_id.extra_income else 0.0,
                    'crew_transfer_ids': [(6, 0, crew.ids)],
                    'sponsor_name': crew.new_vessel_id.id
                }
                self.env['hr.contract'].sudo().create(vals)

            crew.write({
                'state': 'transfer'
            })

    class CrewTransferLine(models.Model):
        _name = 'crew.transfer.line'
        _description = 'crew.transfer.line'

        crew_transfer_id = fields.Many2one('crew.transfer', string='Transfer')
        vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel', related='crew_transfer_id.old_vessel_id')
        employee_id = fields.Many2one('hr.employee', string='Employee')
        contract_id = fields.Many2one('hr.contract', related='employee_id.contract_id')
        factory_manager_ids = fields.Many2many(related='employee_id.factory_manager_ids', string="Factory Manager")
        department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id')
        job_id = fields.Many2one('hr.job', string='Job Position', related='employee_id.job_id')
        days_old = fields.Float(string='Days in Old Vessel', compute='_compute_days_old')
        date_transfer = fields.Date(string='Transfer Date', related='crew_transfer_id.date_transfer', store=True)

        @api.depends('contract_id')
        def _compute_days_old(self):
            """ Computing the days crew member spend in old vessel """
            for crew in self:
                if crew.contract_id:
                    today = fields.Date.today()
                    days_old = (today - crew.contract_id.date_start).days
                    crew.days_old = days_old
                else:
                    crew.days_old = 0
