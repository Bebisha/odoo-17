from odoo import models, fields, api


class KGHRExpenseSheetInherit(models.Model):
    _inherit = "hr.expense.sheet"
    _rec_name = "employee_expense_no"

    employee_expense_no = fields.Char(string="Reference Number")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('employee_expense_no'):
                vals['employee_expense_no'] = self.env['ir.sequence'].next_by_code('employee.expense')
        return super().create(vals_list)

    def add_expenses(self):
        expense_lines = self.env["hr.expense"].search(
            [('employee_id', '=', self.employee_id.id), ('state', 'not in', ['done', 'refused']),
             ('company_id', '=', self.company_id.id)])

        return {
            'name': 'Add: Expense Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'multi.expenses.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sheet_id': self.id,
                'default_employee_id': self.employee_id.id,
                'default_company_id': self.company_id.id,
                'default_expense_ids': [(6, 0, expense_lines.ids)],
            }
        }
