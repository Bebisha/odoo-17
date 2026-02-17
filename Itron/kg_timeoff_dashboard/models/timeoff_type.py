from odoo import models, api, fields


#
#
# class HrEmployee(models.Model):
#     _inherit = 'hr.leave.type'
#
#     time_off_type = fields.Selection(
#         [('is_sick', 'Sick'), ('is_casual', 'Casual'), ('is_unpaid', 'Unpaid'), ('is_annual', 'Annual'),
#          ('is_carry', 'Carry Forward')])


class HrLeave(models.Model):
    _inherit = "hr.leave"

    is_go_back = fields.Boolean(string="Go Back", default=False)

    def action_go_back(self):
        leave_id = self.env['hr.leave'].search(
            [('employee_id', '=', self.employee_id.id), ('holiday_status_id', '=', self.holiday_status_id.id)])

        if leave_id:
            leave_id.write({'is_go_back': False})

        action = self.env.ref('kg_timeoff_dashboard.advanced_timeoff_dashboard_action').read()[0]
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web#action={action['id']}&model=hr.leave&view_type=list",
            'target': 'self',
        }
