# -*- coding:utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import float_round


class KgHrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'


    @api.depends('work_entry_type_id', 'number_of_days', 'number_of_hours', 'payslip_id')
    def _compute_name(self):
        to_check_public_holiday = {
            res[0]: res[1]
            for res in self.env['resource.calendar.leaves']._read_group(
                [
                    ('resource_id', '=', False),
                    ('work_entry_type_id', 'in', self.mapped('work_entry_type_id').ids),
                    ('date_from', '<=', max(self.payslip_id.mapped('date_to'))),
                    ('date_to', '>=', min(self.payslip_id.mapped('date_from'))),
                ],
                ['work_entry_type_id'],
                ['id:recordset']
            )
        }
        for worked_days in self:
            public_holidays = to_check_public_holiday.get(worked_days.work_entry_type_id, '')
            holidays = public_holidays and public_holidays.filtered(lambda p:
               (p.calendar_id.id == worked_days.payslip_id.contract_id.resource_calendar_id.id or not p.calendar_id.id)
                and p.date_from.date() <= worked_days.payslip_id.date_to
                and p.date_to.date() >= worked_days.payslip_id.date_from
                and p.company_id == worked_days.payslip_id.company_id)
            half_day = worked_days._is_half_day()
            if holidays:
                name = (', '.join(holidays.mapped('name')))
            else:
                name = worked_days.work_entry_type_id.name
            worked_days.name = name
