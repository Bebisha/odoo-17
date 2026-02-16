from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HRLeaveAllocationInherit(models.Model):
    _inherit = "hr.leave.allocation"

    def action_refuse(self):
        current_employee = self.env.user.employee_id
        # if any(allocation.state not in ['confirm', 'validate'] for allocation in self):
        #     raise UserError(_('Allocation request must be confirmed or validated in order to refuse it.'))

        days_per_allocation = self.employee_id._get_consumed_leaves(self.holiday_status_id)[0]

        # for allocation in self:
        #     days_taken = days_per_allocation[allocation.employee_id][allocation.holiday_status_id][allocation]['virtual_leaves_taken']
        #     if days_taken > 0:
        #         raise UserError(_('You cannot refuse this allocation request since the employee has already taken leaves for it. Please refuse or delete those leaves first.'))

        self.write({'state': 'refuse', 'approver_id': current_employee.id})
        # If a category that created several holidays, cancel all related
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_refuse()
        self.activity_update()
        return True

    @api.onchange('holiday_type', 'category_id')
    def get_employee(self):
        for rec in self:
            rec.employee_ids = False
            if rec.holiday_type == 'company':
                company_employee_id = self.env['hr.employee'].search([('company_id', '=', rec.mode_company_id.id)])
                for comp in company_employee_id:
                    rec.employee_ids = [(4, comp.id)]

            elif rec.holiday_type == 'department':
                department_employee_id = self.env['hr.employee'].search([('department_id', '=', rec.department_id.id)])
                for dep in department_employee_id:
                    rec.employee_ids = [(4, dep.id)]

            elif rec.holiday_type == 'category':
                if rec.category_id:
                    category_employee_id = self.env['hr.employee'].search(
                        [('category_ids', 'in', rec.category_id.id)])
                    for categ in category_employee_id:
                        rec.employee_ids = [(4, categ.id)]

    def action_validate(self):
        valid_emp = []
        non_valid_emp = []
        for rec in self:
            muslim_religion_id = self.env.ref('kg_mashirah_oil_hrms.muslim_religion').id
            if rec.employee_ids and rec.holiday_status_id == self.env.ref("kg_mashirah_oil_hrms.iddah_leave_type"):
                for emp in rec.employee_ids:
                    if emp.religion_id.id == muslim_religion_id and emp.gender == 'female':
                        valid_emp.append(emp._origin)
                    else:
                        non_valid_emp.append(emp._origin)
                valid_employee = str(valid_emp)[1:-1]
                non_valid_employee = str(non_valid_emp)[1:-1]

                if non_valid_employee:
                    raise ValidationError(_("Iddah leave not applicable for selected employee."))

            return super(HRLeaveAllocationInherit, self).action_validate()
