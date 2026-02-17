# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HRDischarge(models.Model):
    _name = 'hr.discharge'
    _description = 'hr.discharge'

    name = fields.Char(string="Description")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel", related="employee_id.sponsor_name", store=True)
    factory_manager_ids = fields.Many2many(related='employee_id.factory_manager_ids', string="Factory Manager")
    start_date = fields.Date(string="Start Date", required=True)
    date = fields.Date(string="End Date")
    amount = fields.Float(string="Amount")
    state = fields.Selection([('draft', "Draft"), ('approved', "Approved")],
                             string="State", default='draft')

    def action_approve(self):
        """ Discharge Approval """
        for entry in self:
            entry.write({'state': 'approved'})
