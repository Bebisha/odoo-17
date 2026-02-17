# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EntryReportWizard(models.TransientModel):
    _name = 'shop.entry.report.wizard'
    _description = 'shop.entry.report.wizard'

    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
    vessel_id = fields.Many2one('sponsor.sponsor', string='Vessel')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    def get_data(self):
        """ Function to get data for the report """
        for rec in self:
            entry_list = []
            if rec.vessel_id:
                employees = self.env['hr.employee'].search(
                    [('crew', '=', True), ('sponsor_name', '=', rec.vessel_id.id)])
                for employee in employees:
                    entries = self.env['shop.entry'].search(
                        [('employee_id', '=', employee.id), ('date', '>=', rec.date_from),
                         ('date', '<=', rec.date_to)])

                    if entries:
                        amount = sum(entries.mapped('amount'))
                        entry = {
                            'employee': employee.name,
                            'vessel': employee.sponsor_name.name,
                            'amount': amount
                        }
                        entry_list.append(entry)

            else:
                employees = self.env['hr.employee'].search([('crew', '=', True)])
                for employee in employees:
                    entries = self.env['shop.entry'].search(
                        [('employee_id', '=', employee.id), ('date', '>=', rec.date_from),
                         ('date', '<=', rec.date_to)])

                    if entries:
                        amount = sum(entries.mapped('amount'))
                        entry = {
                            'employee': employee.name,
                            'vessel': employee.sponsor_name.name,
                            'amount': amount
                        }
                        entry_list.append(entry)
            return entry_list

    def action_print_pdf(self):
        """ Action to print the pdf report """
        entry_list = self.get_data()
        data = {
            'company': self.company_id,
            'company_name': self.company_id.name,
            'from': self.date_from,
            'to': self.date_to,
            'entry_list': entry_list,
        }
        return self.env.ref('kg_raw_fisheries_hrms.action_shop_entries_report'
                            '').with_context(
            landscape=True).report_action(self, data=data)
