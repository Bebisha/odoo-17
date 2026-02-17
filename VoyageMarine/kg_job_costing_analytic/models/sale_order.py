from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'


    def action_confirm(self):
        res = super().action_confirm()
        for so in self:
            if not so.analytic_account_id:
                so.analytic_account_id = self.env['account.analytic.account'].sudo().create({
                    'name': so.name,
                    'partner_id': so.partner_id.id,
                    'plan_id': self.env.ref('kg_job_costing_analytic.analytic_plan_job').id,
                })
        return res

    def _get_job_costing_lines(self):
        self.ensure_one()

        lines = []
        if not self.analytic_account_id:
            return lines

        analytic_key = str(self.analytic_account_id.id)

        aml_lines = self.env['account.move.line'].search([
            ('move_id.state', '=', 'posted'),
            ('analytic_distribution', '!=', False),
            ('tax_line_id', '=', False),
        ])

        for aml in aml_lines:
            if analytic_key not in (aml.analytic_distribution or {}):
                continue

            percent = aml.analytic_distribution[analytic_key] / 100.0
            allocated_amount = abs(aml.balance) * percent

            lines.append({
                'code': aml.code.upper() if aml.code else '',
                'division': aml.division_id.name if aml.division_id else '',
                'description': aml.name or aml.move_id.name,
                'qty': aml.quantity or 1.0,
                'income': allocated_amount if aml.balance < 0 else 0.0,
                'expense': allocated_amount if aml.balance > 0 else 0.0,
                'date': aml.date,
                'move': aml.move_id.name,
            })

        # ---------------------------------------------------
        # 2️⃣ Labour cost from Timesheets (ONE line per employee)
        # ---------------------------------------------------
        timesheets = self.env['account.analytic.line'].search([
            ('project_id.analytic_account_id', '=', self.analytic_account_id.id),
            ('employee_id', '!=', False),
            ('validated_status', '=', 'validated'),
        ])

        employee_data = {}

        for ts in timesheets:
            employee = ts.employee_id
            contract = employee.contract_id
            if not contract:
                continue

            emp_bucket = employee_data.setdefault(employee.id, {
                'employee': employee,
                'ot_hours': 0.0,
                'ot_rate': 0.0,
                'anchorage_days': 0,
                'anchorage_allowance': contract.anchorage_allowance or 0.0,
                'overseas_days': 0,
                'overseas_allowance': contract.overseas_allowance or 0.0,
            })

            # -----------------------------
            # Overtime calculation
            # -----------------------------
            if ts.ot_hours:
                if contract.ot_wage == 'monthly_fixed':
                    emp_bucket['ot_rate'] = (contract.fixed_ot_allowance or 0.0) / (30 * 8)
                elif contract.ot_wage == 'daily_fixed':
                    emp_bucket['ot_rate'] = (contract.over_time or 0.0) / 8
                elif contract.ot_wage == 'hourly_fixed':
                    emp_bucket['ot_rate'] = contract.hourly_ot_allowance or 0.0

                emp_bucket['ot_hours'] += ts.ot_hours

            # -----------------------------
            # Anchorage (per day)
            # -----------------------------
            if ts.anchorage:
                emp_bucket['anchorage_days'] += 1

            # -----------------------------
            # Overseas (per day)
            # -----------------------------
            if ts.overseas:
                emp_bucket['overseas_days'] += 1

        # ---------------------------------------------------
        # Create job costing lines (ONE per employee per type)
        # ---------------------------------------------------
        for data in employee_data.values():
            employee = data['employee']

            # OT Line
            if data['ot_hours']:
                lines.append({
                    'code': '',
                    'division': '',
                    'description': f"Labour Cost (OT) - {employee.name}",
                    'qty': data['ot_hours'],
                    'income': 0.0,
                    'expense': round(data['ot_hours'] * data['ot_rate'], 2),
                    'move': 'Timesheet',
                })

            # Anchorage Line
            if data['anchorage_days']:
                lines.append({
                    'code': '',
                    'division': '',
                    'description': f"Anchorage Cost - {employee.name}",
                    'qty': data['anchorage_days'],
                    'income': 0.0,
                    'expense': round(data['anchorage_days'] * data['anchorage_allowance'], 2),
                    'move': 'Timesheet',
                })

            # Overseas Line
            if data['overseas_days']:
                lines.append({
                    'code': '',
                    'division': '',
                    'description': f"Overseas Cost - {employee.name}",
                    'qty': data['overseas_days'],
                    'income': 0.0,
                    'expense': round(data['overseas_days'] * data['overseas_allowance'], 2),
                    'move': 'Timesheet',
                })

        return lines

    def _get_job_totals(self):
        lines = self._get_job_costing_lines()
        return {
            'total_income': sum(l['income'] for l in lines),
            'total_expense': sum(l['expense'] for l in lines),
            'profit': sum(l['income'] for l in lines) - sum(l['expense'] for l in lines),
        }