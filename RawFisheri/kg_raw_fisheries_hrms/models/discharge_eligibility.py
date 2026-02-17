# -*- coding: utf-8 -*-

from odoo import fields, models, api


class DischargeEligibility(models.Model):
    _name = 'discharge.eligibility'
    _description = 'discharge.eligibility'

    name = fields.Char(string='Name')
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    department_id = fields.Many2one('hr.department', string="Department")
    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel")
    quantity = fields.Float(string="Discharge Quantity")

    @api.onchange('vessel_id')
    def _onchange_vessel_id(self):
        """ Function to pass employees on the basis of vessel """
        if self.vessel_id:
            employees = self.env['hr.employee'].search([('sponsor_name', '=', self.vessel_id.id)])
            self.employee_ids = [(6, 0, employees.ids)]
