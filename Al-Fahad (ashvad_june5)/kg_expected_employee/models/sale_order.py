from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    employee_id = fields.Many2one('expected.employee', string='Employee')
    cost_center = fields.Many2one('employee.department', 'Cost Center', compute='_compute_department_id', store=True)

    @api.depends('employee_id')
    def _compute_department_id(self):
        for order in self:
            if order.employee_id:
                order.cost_center = order.employee_id.department
            else:
                order.cost_center = False
