# -- coding: utf-8 --
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PayrollReportConsolidated(models.Model):
    """ Model to show department wise payroll report """
    _name = 'payroll.report.consolidated'
    _description = 'payroll.report.consolidated'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    vessel_id = fields.Many2one('sponsor.sponsor', related='employee_id.sponsor_name', string="Vessel", store=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    payslip_total = fields.Float(string='Payslip Total', compute='_compute_payslip_total', store=True)
    date_from = fields.Date(string="Payslip Date From", related="payslip_id.date_from", store=True)

    @api.depends('payslip_id')
    def _compute_payslip_total(self):
        for record in self:
            record.payslip_total = sum(record.payslip_id.line_ids.mapped('total'))

    def load_payslip_details(self):
        """ Function to load data in the pivot view """
        payslips = self.env['hr.payslip'].sudo().search([], order='date_from desc')


        domain_list = []
        for payslip in payslips:
            record = self.env['payroll.report.consolidated'].sudo().create({
                'employee_id': payslip.employee_id.id,
                'payslip_id': payslip.id,
            })
            domain_list.append(record.id)

        return {
            'name': _('Payroll Report'),
            'view_type': 'form',
            'view_mode': 'pivot,tree',
            'domain': [('id', 'in', domain_list)],
            'context': {
                'search_default_groupby_vessel_id': 1,
                'search_default_groupby_department_id': 1,
                'search_default_groupby_date_from:month': 1
            },
            'res_model': 'payroll.report.consolidated',
            'type': 'ir.actions.act_window',
            'target': 'main',
        }
