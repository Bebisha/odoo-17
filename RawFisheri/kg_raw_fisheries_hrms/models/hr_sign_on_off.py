# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HRSignOnOff(models.Model):
    """ Logging Crew Sign on and Sign off """
    _name = 'sign.on.off'
    _description = 'sign.on.off'
    _rec_name = "contract_reference"

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        domain=lambda self: self._get_employee_domain(),
        required=True
    )
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    sign_on = fields.Date(string="Sign On")
    sign_off = fields.Date(string="Sign Off")
    factory_manager_ids = fields.Many2many(related='employee_id.factory_manager_ids', string="Factory Manager")
    vessel_id = fields.Many2one('sponsor.sponsor', string="Vessel", related="employee_id.sponsor_name", store=True)
    state = fields.Selection([('draft', "Draft"), ('to_approve', "To Approve"), ('approved', "Approved")],
                             string="State", default='draft')
    contract_reference = fields.Char(string="Contract Reference")

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    'You cannot delete a Employee Sign On/Off which is not in draft state')
        return super(HRSignOnOff, self).unlink()

    @api.constrains('employee_id')
    def get_sign_on_from_contract(self):
        """ To get sign on date from contract if contract is already created """
        for rec in self:
            if rec.employee_id.contract_id and not rec.sign_on:
                rec.write({
                    'sign_on': rec.employee_id.contract_id.date_start or None,
                    'contract_reference': rec.employee_id.contract_id.name
                })

    @api.model
    def _get_employee_domain(self):
        """ Domain set for field employee_id """
        if self.env.ref('kg_raw_fisheries_hrms.hr_manager').id in self.env.user.groups_id.ids:
            return [('crew', '=', True)]
        else:
            return [('factory_manager_ids.user_id', '=', self.env.user.id)]

    def submit_for_approval(self):
        """ Updates end date for already existing contracts and create new contract if running contract doesn't exist"""
        for rec in self:
            if rec.state == 'draft':
                rec.state = 'to_approve'
                if rec.employee_id.contract_id:
                    rec.employee_id.contract_id.date_end = rec.sign_off
                    rec.contract_reference = rec.employee_id.contract_id.name
                else:
                    vals = {
                        'name': rec.contract_reference,
                        'state': 'open',
                        'employee_id': rec.employee_id.id,
                        'date_start': rec.sign_on,
                        'date_end': rec.sign_off,
                        'wage': 0.0,
                        'sponsor_name': self.vessel_id.id,
                        'sign_on_off_id': rec.id
                    }
                    self.env['hr.contract'].sudo().create(vals)

    def action_approve(self):
        for rec in self:
            if rec.state == 'draft':
                if not rec.contract_reference:
                    raise ValidationError("Add the Contract Reference !!")
                rec.state = 'to_approve'
                if rec.employee_id.contract_id:
                    rec.employee_id.contract_id.date_end = rec.sign_off
                else:
                    vals = {
                        'name': rec.contract_reference,
                        'state': 'open',
                        'employee_id': rec.employee_id.id,
                        'date_start': rec.sign_on,
                        'date_end': rec.sign_off,
                        'wage': 0.0,
                        'sponsor_name': rec.vessel_id.id,
                        'sign_on_off_id': rec.id
                    }
                    self.env['hr.contract'].sudo().create(vals)

            rec.state = 'approved'
