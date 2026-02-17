from odoo import models, fields


class KGHRPayslipLineInherit(models.Model):
    _inherit = "hr.payslip.line"

    is_alw = fields.Boolean(default=False, string="Is Allowance", compute="compute_is_alw")
    is_ded = fields.Boolean(default=False, string="Is Deduction", compute="compute_is_ded")

    def compute_is_alw(self):
        for rec in self:
            if rec.category_id.id == self.env.ref('hr_payroll.BASIC').id:
                rec.is_alw = True
            elif rec.category_id.id == self.env.ref('hr_payroll.ALW').id:
                rec.is_alw = True
            else:
                rec.is_alw = False

    def compute_is_ded(self):
        for rec in self:
            if rec.category_id.id == self.env.ref('hr_payroll.DED').id:
                rec.is_ded = True
            else:
                rec.is_ded = False
