# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime, time, date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import format_date
from odoo.tools.safe_eval import pytz


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    vessel_id = fields.Many2one('sponsor.sponsor')

    @api.depends('department_id', 'vessel_id')
    def _compute_employee_ids(self):
        """ Overridden to add employee domain on the basis of vessel and batch date range """
        for wizard in self:
            domain = wizard._get_available_contracts_domain()

            if wizard.department_id:
                domain = expression.AND([
                    domain,
                    [('department_id', 'child_of', wizard.department_id.id)]
                ])

            if wizard.vessel_id:
                domain = expression.AND([
                    domain,
                    [('sponsor_name', '=', wizard.vessel_id.id)]
                ])

            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

            if not payslip_run:
                wizard.employee_ids = self.env['hr.employee']
                continue

            date_from = payslip_run.date_start
            date_to = payslip_run.date_end

            employee_entries = self.env['hr.employee.entry'].search([
                '|',
                '&', ('start_date', '>=', date_from), ('start_date', '<=', date_to),
                '&', ('end_date', '>=', date_from), ('end_date', '<=', date_to),
                ('vessels_id', '=', wizard.vessel_id.id) if wizard.vessel_id else ('id', '!=', False),
            ])
            employee_ids = employee_entries.mapped('employee_id.id')

            domain = expression.AND([
                domain,
                [('id', 'in', employee_ids)]
            ])

            employees = self.env['hr.employee'].search(domain)
            managed_employee_ids = employees.filtered(
                lambda e: e.parent_id and e.parent_id.user_id == self.env.user).ids

            wizard.employee_ids = employees.filtered(lambda e: e.id in managed_employee_ids)

    def compute_sheet(self):
        """ Overridden to reflect employee entries in Batch Payslip """
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            today = fields.date.today()
            first_day = today + relativedelta(day=1)
            last_day = today + relativedelta(day=31)
            if from_date == first_day and end_date == last_day:
                batch_name = from_date.strftime('%B %Y')
            else:
                batch_name = _('From %s to %s', format_date(self.env, from_date), format_date(self.env, end_date))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': batch_name,
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        employees -= payslip_run.slip_ids.employee_id
        success_result = {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
        if not employees:
            return success_result

        Payslip = self.env['hr.payslip']

        contracts = employees._get_contracts(
            payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
        ).filtered(lambda c: c.active)
        contracts.generate_work_entries(payslip_run.date_start, payslip_run.date_end)

        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end + relativedelta(days=1)),
            ('date_stop', '>=', payslip_run.date_start + relativedelta(days=-1)),
            ('employee_id', 'in', employees.ids),
        ])
        for slip in payslip_run.slip_ids:
            slip_tz = pytz.timezone(slip.contract_id.resource_calendar_id.tz)
            utc = pytz.timezone('UTC')
            date_from = slip_tz.localize(datetime.combine(slip.date_from, time.min)).astimezone(utc).replace(
                tzinfo=None)
            date_to = slip_tz.localize(datetime.combine(slip.date_to, time.max)).astimezone(utc).replace(tzinfo=None)
            payslip_work_entries = work_entries.filtered_domain([
                ('contract_id', '=', slip.contract_id.id),
                ('date_stop', '<=', date_to),
                ('date_start', '>=', date_from),
            ])
            payslip_work_entries._check_undefined_slots(slip.date_from, slip.date_to)

        if self.structure_id.type_id.default_struct_id == self.structure_id:
            work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
            if work_entries._check_if_error():
                work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])
                for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
                    work_entries_by_contract[work_entry.contract_id] |= work_entry
                for contract, work_entries in work_entries_by_contract.items():
                    conflicts = work_entries._to_intervals()
                    time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in conflicts._items]])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Some work entries could not be validated.'),
                        'message': _('Time intervals to look for:%s', time_intervals_str),
                        'sticky': False,
                    }
                }

        default_values = Payslip.default_get(Payslip.fields_get())
        payslips_vals = []

        for contract in self._filter_contracts(contracts):
            if not contract.date_end:
                date_end = payslip_run.date_end
            elif contract.date_end and contract.date_end >= payslip_run.date_end:
                date_end = payslip_run.date_end
            elif contract.date_end and contract.date_end <= payslip_run.date_end:
                date_end = contract.date_end
            else:
                date_end = False

            if contract.date_start and contract.date_start <= payslip_run.date_start:
                date_start = payslip_run.date_start
            elif contract.date_start and contract.date_start >= payslip_run.date_start:
                date_start = contract.date_start
            else:
                date_start = False


            employee_entries = self.env['hr.employee.entry'].search(
                [('employee_id', '=', contract.employee_id.id), ('start_date', '>=', date_start),
                 ('end_date', '<=', date_end), ('state', '=', 'approved')]
            )
            pre_payments = self.env['salary.pre.payment'].search(
                [('employee_id', '=', contract.employee_id.id), ('paid_date', '>=', date_start),
                 ('paid_date', '<=', date_end), ('state', '=', 'approved')]
            )
            pending_salaries = self.env['pending.salary'].search(
                [('employee_id', '=', contract.employee_id.id), ('settlement_date', '>=', date_start),
                 ('settlement_date', '<=', date_end), ('state', '=', 'approved')]
            )

            shop_deduction = sum(employee_entries.mapped('shop_deduction'))
            over_time = sum(employee_entries.mapped('over_time'))
            bonus = sum(employee_entries.mapped('bonus'))
            discharge_allowance = sum(employee_entries.mapped('discharge_qty'))
            holiday_allowance = sum(employee_entries.mapped('holiday_allowance'))
            penalty = sum(employee_entries.mapped('penalty'))
            pending_salaries = sum(pending_salaries.mapped('amount'))


            pre_payment_deduction = 0.0
            for pre_payment in pre_payments:
                payment_currency = pre_payment.currency_id
                amount = pre_payment.amount
                if pre_payment.currency_id != contract.foreign_currency_id:
                    amount = payment_currency._convert(
                        amount,
                        contract.foreign_currency_id,
                        self.env.company,
                        fields.Date.today()
                    )
                pre_payment_deduction += amount

            allowance_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'REIMBURSEMENT')])
            over_time_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'OVERTIME')])
            bonus_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'EXTRAINCOME')])
            discharge_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'DISCHARGE')])
            deduction_type_id = self.env['hr.payslip.input.type'].search([('code', '=', 'DEDUCTION')])

            inputs = []
            if over_time:
                if contract.foreign_currency_id and contract.foreign_currency_id != contract.currency_id:
                    over_time = contract.currency_id._convert(
                        over_time, contract.foreign_currency_id, self.env.company, fields.Date.today()
                    )
                inputs.append({
                    'name': 'Over Time',
                    'code': 'OVERTIME',
                    'input_type_id': over_time_type_id.id,
                    'amount': over_time,
                    'contract_id': contract.employee_id.contract_id.id,
                })

            if bonus:
                if contract.foreign_currency_id and contract.foreign_currency_id != contract.currency_id:
                    bonus = contract.currency_id._convert(
                        bonus, contract.foreign_currency_id, self.env.company, fields.Date.today()
                    )
                inputs.append({
                    'name': 'Extra Income',
                    'code': 'EXTRAINCOME',
                    'input_type_id': bonus_type_id.id,
                    'amount': bonus,
                    'contract_id': contract.employee_id.contract_id.id,
                })

            if discharge_allowance:
                if contract.foreign_currency_id and contract.foreign_currency_id != contract.currency_id:
                    discharge_allowance = contract.currency_id._convert(
                        discharge_allowance, contract.foreign_currency_id, self.env.company, fields.Date.today()
                    )
                inputs.append({
                    'name': 'Discharge',
                    'code': 'DISCHARGE',
                    'input_type_id': discharge_type_id.id,
                    'amount': discharge_allowance,
                    'contract_id': contract.employee_id.contract_id.id,
                })

            if holiday_allowance:
                if contract.foreign_currency_id and contract.foreign_currency_id != contract.currency_id:
                    holiday_allowance = contract.currency_id._convert(
                        holiday_allowance, contract.foreign_currency_id, self.env.company, fields.Date.today()
                    )
                inputs.append({
                    'name': 'Holiday Allowance',
                    'code': 'REIMBURSEMENT',
                    'input_type_id': allowance_type_id.id,
                    'amount': holiday_allowance,
                    'contract_id': contract.employee_id.contract_id.id,
                })

            if penalty:
                if contract.foreign_currency_id and contract.foreign_currency_id != contract.currency_id:
                    penalty = contract.currency_id._convert(
                        penalty, contract.foreign_currency_id, self.env.company, fields.Date.today()
                    )
                inputs.append({
                    'name': 'Penalty',
                    'code': 'DEDUCTION',
                    'input_type_id': deduction_type_id.id,
                    'amount': penalty,
                    'contract_id': contract.employee_id.contract_id.id,
                })

            if shop_deduction:
                if contract.foreign_currency_id and contract.foreign_currency_id != contract.currency_id:
                    shop_deduction = contract.currency_id._convert(
                        shop_deduction, contract.foreign_currency_id, self.env.company, fields.Date.today()
                    )
                inputs.append({
                    'name': 'Shop Deduction',
                    'code': 'DEDUCTION',
                    'input_type_id': deduction_type_id.id,
                    'amount': shop_deduction,
                    'contract_id': contract.employee_id.contract_id.id,
                })

            if pre_payment_deduction:
                inputs.append({
                    'name': 'Salary Pre Payment',
                    'code': 'DEDUCTION',
                    'input_type_id': deduction_type_id.id,
                    'amount': pre_payment_deduction,
                    'contract_id': contract.employee_id.contract_id.id,
                })

            if pending_salaries:
                if contract.foreign_currency_id and contract.foreign_currency_id != contract.currency_id:
                    pending_salaries = contract.currency_id._convert(
                        pending_salaries, contract.foreign_currency_id, self.env.company, fields.Date.today()
                    )
                inputs.append({
                    'name': 'Pending Salaries',
                    'code': 'REIMBURSEMENT',
                    'input_type_id': allowance_type_id.id,
                    'amount': pending_salaries,
                    'contract_id': contract.employee_id.contract_id.id,
                })

            values = dict(default_values, **{
                'name': _('New Payslip'),
                'employee_id': contract.employee_id.id,
                'payslip_run_id': payslip_run.id,
                'date_from': date_start,
                'date_to': date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
                'input_line_ids': [(0, 0, input_val) for input_val in inputs],
            })
            payslips_vals.append(values)

        payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
        payslips._compute_name()
        payslips.compute_sheet()
        payslip_run.state = 'verify'

        return success_result

