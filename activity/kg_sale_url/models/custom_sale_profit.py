# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import fields, models, api


from odoo.addons.web_approval.models.approval_mixin import _APPROVAL_STATES

class SaleProfit(models.Model):
    _name = 'sale.profit'
    _description = 'Sale Profit Report'
    _inherit = ['approval.mixin']

    name = fields.Char(string="Name")
    product_id = fields.Many2one('product.product', string='Product / Service')
    code = fields.Char(string='Code')
    date = fields.Date(string='Date')
    unit_cost = fields.Float(string='Unit Cost')
    total_cost = fields.Float(string='Total Cost')
    sales_price = fields.Float(string='Sales Price')
    quantity = fields.Float(string='Quantity')
    proposed_amount = fields.Float(string='Proposed Amount')
    invoiced_amount = fields.Float(string='Invoiced Amount')
    paid_amount = fields.Float(string='Paid Amount')
    # sales_commission = fields.Float(string='Sales Commission', compute='_compute_sales_commission')
    sales_commission = fields.Float(string='Sales Commission')
    # hr_cost = fields.Float(string='HR Cost', compute='_compute_hr_cost')
    hr_cost = fields.Float(string='HR Cost')
    net_margin_percent = fields.Float(string='Net Margin(%)')
    # net_margin_percent = fields.Float(string='Net Margin(%)', compute='_compute_net_margin_percent', store=True)
    # net_margin_amount = fields.Float(string='Net Margin Amount', compute='_compute_net_margin_amount', store=True)
    net_margin_amount = fields.Float(string='Net Margin Amount')
    approvals = fields.Json('Approval Flow')
    approval_state = fields.Selection(string='Approval Status', selection=_APPROVAL_STATES, required=False, copy=False,
                                      is_approval_state=True, tracking=True)
    #
    def sale_profit_report(self):
        print("ppppppppppppppppppp")
        year = self._context.get('year', datetime.now().year)
        print(year)
        # date_from = f"{year}-01-01"
        # date_to = f"{year + 1}-01-01"

        list_val = []
        for sale in self.env['sale.order'].search([('state', '=', 'sale')]):
            for order_line in sale.order_line:

                if order_line:
                    proposed_amount = order_line.price_unit * order_line.product_uom_qty
                    invoiced_amount = order_line.price_subtotal
                    total_cost = order_line.product_id.standard_price * sum(line.product_uom_qty for line in sale.order_line)
                    net_margin_percentage = ((order_line.price_unit - total_cost) / order_line.price_unit) * 100 if order_line.price_unit != 0 else 0
                    paid_amount = sum(payment.invoice_outstanding_credits_debits_widget for payment in sale.invoice_ids)
                    net_margin_amount = order_line.product_id.list_price - order_line.product_id.standard_price
                    vals = {
                        'name': sale.partner_id.name,
                        # 'product_id': order_line.product_id.name,
                        'code': order_line.product_id.default_code,
                        'date': sale.date_order,
                        'product_id': order_line.product_id.id,
                        'unit_cost': order_line.product_id.standard_price,
                        'sales_price': order_line.price_unit,
                        'quantity': sum(line.product_uom_qty for line in sale.order_line),
                        'proposed_amount': proposed_amount,
                        'invoiced_amount': invoiced_amount,
                        'sales_commission': order_line.price_subtotal * 0.2,
                        'net_margin_percent':net_margin_percentage,
                        'paid_amount':sale.amount_paid,
                        'net_margin_amount':net_margin_amount,
                        'total_cost': order_line.product_id.standard_price * sum(line.product_uom_qty for line in sale.order_line),

                    }
                    print('vals',vals)
                    obj_val = self.env['sale.profit'].create(vals)
                    list_val.append(obj_val.id)

        return {
            'name': 'Sale profit',
            'view_mode': 'tree,graph',
            'domain': [('id', 'in', list_val)],
            'res_model': 'sale.profit',
            'type': 'ir.actions.act_window',
            'context': { "group_by": "date:year"},
            'target': 'main'
        }

    # def create_sale(self, vals):
    #     sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
    #     products = self.env['product.template'].search([])
    #     list_val = []
    #
    #     for product in products:
    #         date = ''
    #         for sale in sale_orders.filtered(
    #                 lambda s: any(l.product_id.product_tmpl_id == product for l in s.order_line)):
    #             date = sale.date_order
    #             list_val.append({
    #                 'name': product.name,
    #                 'code': product.default_code,
    #                 'date': date,
    #                 'unit_cost': product.standard_price,
    #                 'sales_price': product.amount_total,
    #                 'quantity': sum(line.product_uom_qty for line in product.order_line),
    #                 'proposed_amount': product.amount_untaxed,
    #                 'invoiced_amount': product.amount_total,
    #                 'total_cost': product.standard_price * sum(line.product_uom_qty for line in product.order_line),
    #             })
    #             self.env['sale.profit'].create({
    #                 'name': product.name,  # Adjust accordingly based on what you need to create in sale.profit
    #                 'date': date,  # Adjust accordingly based on what you need to create in sale.profit
    #                 # Add other fields as needed for sale.profit creation
    #             })
    #
    #     return {
    #         'name': 'Sales Profit',
    #         'view_mode': 'tree,graph',
    #         'res_model': 'sale.profit',
    #         'type': 'ir.actions.act_window',
    #         'domain': [('id', 'in', [val['id'] for val in list_val])],
    #         'context': {},
    #         'target': 'main'
    #     }

    # @api.model
    # def create(self, vals):
    #     sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
    #     products = self.env['product.template'].search([])
    #     for product in products:
    #         date = ''
    #         for sale in sale_orders.filtered(
    #                 lambda s: s.order_line.filtered(lambda l: l.product_id.product_tmpl_id == product)):
    #             date = sale.date_order
    #         vals = {
    #             'name': product.name,
    #             'code': product.default_code,
    #             'date': date,
    #             'unit_cost': product.standard_price,
    #         }
    #         self.env['sale.profit'].create(vals)
    #
    #     return super(SaleProfit, self).create(vals)

    # @api.depends('sales_price', 'unit_cost', 'quantity')
    # def _compute_sales_commission(self):
    #     for record in self:
    #         if record.sales_price and record.unit_cost and record.quantity:
    #             record.sales_commission = 0.2 * (record.sales_price - record.unit_cost) * record.quantity
    #         else:
    #             record.sales_commission = 0.0
    #
    # @api.depends('hr_cost')
    # def _compute_hr_cost(self):
    #     for record in self:
    #         # Replace with your logic to compute HR cost based on salary
    #         record.hr_cost = 0.0  # Example: replace with actual computation
    #
    # @api.depends('sales_price', 'unit_cost', 'quantity', 'total_cost')
    # def _compute_net_margin_percent(self):
    #     for record in self:
    #         if record.sales_price and record.unit_cost and record.quantity and record.total_cost:
    #             sales_amount = record.sales_price * record.quantity
    #             cost = record.total_cost
    #             if sales_amount > 0:
    #                 record.net_margin_percent = ((sales_amount - cost) / sales_amount) * 100
    #             else:
    #                 record.net_margin_percent = 0.0
    #         else:
    #             record.net_margin_percent = 0.0
    #
    # @api.depends('sales_price', 'unit_cost', 'quantity', 'total_cost')
    # def _compute_net_margin_amount(self):
    #     for record in self:
    #         if record.sales_price and record.unit_cost and record.quantity and record.total_cost:
    #             sales_amount = record.sales_price * record.quantity
    #             cost = record.total_cost
    #             record.net_margin_amount = sales_amount - cost
    #         else:
    #             record.net_margin_amount = 0.0


    # def create_sale(self):
    #     sale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
    #
    #     for sale in sale_orders:
    #         vals = {
    #             'name': sale.name,
    #             'date': sale.date_order.strftime('%Y-%m-%d'),
    #         }
    #
    #         total_cost = 0.0
    #         sales_price = 0.0
    #         quantity = 0
    #         proposed_amount = 0.0
    #         invoiced_amount = 0.0
    #         paid_amount = 0.0
    #         sales_commission = 0.0
    #         hr_cost = 0.0
    #         net_margin_percentage = 0.0
    #         net_margin_amount = 0.0
    #
    #         for line in sale.order_line:
    #             total_cost += line.product_id.standard_price * line.product_uom_qty
    #             sales_price += line.price_subtotal
    #             quantity += line.product_uom_qty
    #             proposed_amount += line.price_unit * line.product_uom_qty
    #             invoiced_amount += line.price_subtotal
    #
    #             paid_amount = sum(payment.amount for payment in sale.payment_ids)
    #             sales_commission = sales_price * 0.2  # Assuming 20% commission
    #             hr_cost = sum(employee.contract_id.wage for employee in sale.employee_ids)
    #             net_margin_percentage = ((sales_price - total_cost) / sales_price) * 100 if sales_price != 0 else 0
    #             net_margin_amount = sales_price - total_cost
    #
    #         vals.update({
    #             'unit_cost': total_cost / quantity if quantity != 0 else 0,
    #             'total_cost': total_cost,
    #             'sales_price': sales_price,
    #             'quantity': quantity,
    #             'proposed_amount': proposed_amount,
    #             'invoiced_amount': invoiced_amount,
    #             'paid_amount': paid_amount,
    #             'sales_commission': sales_commission,
    #             'hr_cost': hr_cost,
    #             'net_margin_percent': net_margin_percentage,
    #             'net_margin_amount': net_margin_amount,
    #         })
    #
    #         # Create a record in the 'sale.profit' model using vals
    #         self.env['sale.profit'].create(vals)
    #
    #     # Return the action dictionary to open the view after creating records
    #     return {
    #         'name': 'Sales Profit',
    #         'view_mode': 'tree,graph',
    #         'res_model': 'sale.profit',
    #         'type': 'ir.actions.act_window',
    #         'context': {},  # Add context as needed
    #         'target': 'main'
    #     }

    # @api.model
    # def create_sale(self, vals):
    #     vals=[]
    #     sale_order = self.env['sale.order'].browse(vals.get('order_id'))
    #     if sale_order:
    #         product = sale_order.order_line[0].product_id
    #         vals.update({
    #             'name': product.name,
    #             'code': product.default_code,
    #             'date': sale_order.date_order,
    #             'unit_cost': product.standard_price,
    #             'sales_price': sale_order.amount_total,
    #             'quantity': sum(line.product_uom_qty for line in sale_order.order_line),
    #             'proposed_amount': sale_order.amount_untaxed,
    #             'invoiced_amount': sale_order.amount_total,
    #             'total_cost': product.standard_price * sum(line.product_uom_qty for line in sale_order.order_line),
    #         })
    #         print(vals)
    #     return {
    #         'name': 'Vendor Wise Pending Order',
    #         'view_mode': 'tree',
    #         'domain': [('id', 'in', vals)],
    #         'res_model': 'sale.profit',
    #         'type': 'ir.actions.act_window',
    #         'context': {},
    #         'target': 'main'
    #     }

    # @api.model


    # ale_orders = self.env['sale.order'].search([('state', '=', 'sale')])
    # products = self.env['product.template'].search([])
    # for product in products:
    #     date = ''
    #     for sale in sale_orders:
    #         date = sale.date_order
    #         for lines in sale.order_line:
    #             if lines.product_id.product_tmpl_id == product:
    #                 print(lines.product_id.name, lines.product_id.id, 'pppppppppppppppp')
    #     vals = {
    #         'product_id': product.id,
    #         'date': date,
    #     }
    #     self.env['sale.profit'].create(vals)
    # @api.model
    # def create_sale(self):
    #     list_val = []
    #     for sale in self.env['sale.order'].search([('state', '=', 'sale')]):
    #
    #         total_cost = 0.0
    #         sales_price = 0.0
    #         quantity = 0
    #         proposed_amount = 0.0
    #         invoiced_amount = 0.0
    #         paid_amount = 0.0
    #         sales_commission = 0.0
    #         hr_cost = 0.0
    #         net_margin_percentage = 0.0
    #         net_margin_amount = 0.0
    #         for line in sale.order_line:
    #             total_cost += line.product_id.standard_price * line.product_uom_qty
    #             sales_price += line.price_subtotal
    #             quantity += line.product_uom_qty
    #             proposed_amount += line.price_unit * line.product_uom_qty
    #             invoiced_amount += line.price_subtotal
    #
    #             # paid_amount = sum(payment.amount for payment in sale.payment_ids)
    #             sales_commission = sales_price * 0.2  # Assuming 20% commission
    #             # hr_cost = sum(employee.contract_id.wage for employee in sale.employee_ids)
    #             net_margin_percentage = ((sales_price - total_cost) / sales_price) * 100 if sales_price != 0 else 0
    #             net_margin_amount = sales_price - total_cost
    #             if total_cost == 0:
    #                 vals = {
    #                     'unit_cost': total_cost / quantity if quantity != 0 else 0,
    #                     'total_cost': total_cost,
    #                     'sales_price': sales_price,
    #                     'quantity': quantity,
    #                     'proposed_amount': proposed_amount,
    #                     'invoiced_amount': invoiced_amount,
    #                     'paid_amount': paid_amount,
    #                     'sales_commission': sales_commission,
    #                     'hr_cost': hr_cost,
    #                     'net_margin_percent': net_margin_percentage,
    #                     'net_margin_amount': net_margin_amount,
    #                 }
    #                 obj_val = self.env['vendor.purchase.report'].create(vals)
    #                 list_val.append(obj_val.id)
    #
    #     return {
    #         'name': 'Vendor Wise Pending Order',
    #         'view_mode': 'tree',
    #         'domain': [('id', 'in', list_val)],
    #         'res_model': 'sale.profit',
    #         'type': 'ir.actions.act_window',
    #         'context': {},
    #         'target': 'main'
    #     }
