# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HRContract(models.Model):
    _inherit = 'hr.contract'

    name = fields.Char('Contract Reference', required=True, default=lambda self: _('New'), readonly=True)
    flight_allowance_ids = fields.One2many('flight.allowance.lines', 'contract_id', copy=False,
                                           string='Flight Allowance')
    designation_id = fields.Many2one('hr.designation', string="Designation")

    @api.depends('employee_id', 'name')
    def _compute_display_name(self):
        for rec in self:
            if rec.name and rec.employee_id:
                rec.display_name = f"{rec.name}  -  {rec.employee_id.name}"
            elif rec.name:
                rec.display_name = rec.name
            else:
                rec.display_name = "Undefined"

    @api.model
    def create(self, vals):
        """ Set contract reference number with country-based prefix. """
        if vals.get('company_id'):
            company_obj = self.env['res.company'].browse(vals.get('company_id'))
            country_code = company_obj.country_code
            country_sequence_mapping = {
                'US': 'hr_contract_us',
                'BH': 'hr_contract_bh',
                'IN': 'hr_contract_in',
                'OM': 'hr_contract_om',
                'AE': 'hr_contract_dubai'
            }
            sequence_code = country_sequence_mapping.get(country_code, None)
            if sequence_code:
                vals['name'] = self.env['ir.sequence'].next_by_code(sequence_code) or 'New'
            else:
                vals['name'] = 'New'
        return super(HRContract, self).create(vals)


class FlightAllowance(models.Model):
    _name = 'flight.allowance.lines'

    date = fields.Date(string='Date', copy=False)
    contract_id = fields.Many2one('hr.contract', string='Contract')
    amount = fields.Float(string='Amount', copy=False)
    status = fields.Selection([('paid', 'Paid'), ('not_paid', 'Not Paid')], string='Status', default='not_paid')
    description = fields.Char(string='Description')
