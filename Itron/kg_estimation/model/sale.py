from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
  _inherit = 'sale.order'

  estimation_id = fields.Many2one('sales.estimation','Estimation')

  # def action_confirm(self):
  #   for order in self:
  #     if (order.estimation_id.total_cost > order.amount_total):
  #       raise UserError(_('The total amount is less than the estimated cost'))
  #     rec = self.env['sale.order'].search([('estimation_id', '=', order.estimation_id.id)])
  #     val = 0
  #     for data in rec:
  #       if data.state == 'sale':
  #         val = 1
  #     if val == 1:
  #       raise UserError(_('The corresponding estimation ' + order.estimation_id.name + ' has  another an approved Sale Order'))
  #     order.estimation_id.order_id = order.id
  #   return super(SaleOrder, self).action_confirm()