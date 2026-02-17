from odoo import models, fields


class KGMultiExpensesWizard(models.TransientModel):
    _name = "multi.expenses.wizard"

    name = fields.Char(string="Reference")
    sheet_id = fields.Many2one("hr.expense.sheet", string="Sheet")
    expense_ids = fields.Many2many("hr.expense", string="Expenses")
    employee_id = fields.Many2one("hr.employee", string="Employee")
    company_id = fields.Many2one("res.company", string="Company")

    def select_expenses(self):
        if self.expense_ids and self.sheet_id:
            selected_expenses = self.expense_ids.filtered(lambda exp: exp.is_select)
            if selected_expenses:
                self.sheet_id.write({
                    'expense_line_ids': [(4, exp.id) for exp in selected_expenses]
                })
