# -*- coding: utf-8 -*-
from odoo import models, api, fields, _


class KGExchange(models.Model):
    _name = 'kg.exchange'
    _description = 'Exchange'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency')


class KGInvestmentType(models.Model):
    _name = 'kg.investment.type'
    _description = 'Investment Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    stock_valuation_account_id = fields.Many2one('account.account', 'Stock Valuation Account')
    stock_journal_id = fields.Many2one('account.journal', 'Stock Journal')
    stock_input_account_id = fields.Many2one('account.account', 'Stock Output Account')
    stock_output_account_id = fields.Many2one('account.account', 'Stock Input Account')
    market_account_id = fields.Many2one('account.account','Account')
    is_bond = fields.Boolean('Bond',default=False)
    is_fvtpl = fields.Boolean('FVTPL',default=False)
    is_fvoci = fields.Boolean('FVOCI',default=False)


class KGInvestmentEntry(models.Model):
    _name = 'kg.investment.entry'
    _description = 'Investment Entry'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Investment Name', required=True)
    isin_code = fields.Char(string='ISIN Code')
    investment_type = fields.Many2one('kg.investment.type', string='Investment Type', required=True)
    country_id = fields.Many2one('res.country', string='Country')
    currency_id = fields.Many2one('res.currency', string='Currency')
    account_id = fields.Many2one('account.account', string='Account', )
    revaluation_account_id = fields.Many2one('account.account', string='Revaluation Reserve Account')
    purchase_id = fields.Many2one('kg.purchase.order')
    sale_id = fields.Many2one('kg.sale.order')
    sale_order_ids = fields.Many2many('kg.sale.order', string='Sale Orders', compute='_compute_sale_order_ids')
    purchase_order_ids = fields.Many2many('kg.purchase.order', string='Purchase Orders',
                                          compute='_compute_purchase_order_ids')
    kg_stock_quants = fields.One2many('kg.stock.quant', 'investment_id', string='Stock Quants')
    face_value = fields.Float(string='Face Value',compute='compute_face_value',digits=(10,6))
    market_value = fields.Float(string='Market Value',digits=(10,6))

    qty_on_hand = fields.Float(string='Quantity On Hand', compute='_compute_qty_on_hand',)
    fvoci = fields.Boolean(related='investment_type.is_fvoci')



    @api.depends('qty_on_hand')
    def compute_face_value(self):
        for rec in self:
            rec.face_value = 0.0
            stock_quant = self.env['kg.stock.quant'].search([('investment_id', '=', rec.id),('is_purchase','=',True),],order='id desc', limit=1)
            if stock_quant:
                rec.face_value = stock_quant.avg_cost
            # print("22222222")
            # market_rates = self.env['market.rate.updation'].search([
            #     ('investment_type_id', '=', rec.investment_type), ])
            # for market_rate in market_rates:
            #     if market_rate.market_rate_line_id.investment_id == rec.id:
            #         rec.face_value = market_rate.market_rate
            #         break  # Exit the loop after finding the correct match
            # else:
            #     # Optional: Handle case where no matching record was found
            #     pass

    @api.depends('kg_stock_quants')
    def _compute_qty_on_hand(self):
        for investment in self:
            existing_qty = sum(quant.quantity for quant in investment.kg_stock_quants)
            purchased_qty = sum(quant.quantity for quant in investment.kg_stock_quants if quant.cost_price > 0)
            sold_qty = sum(quant.quantity for quant in investment.kg_stock_quants if
                           quant.cost_price < 0)  # Assuming negative cost_price indicates sales

            # investment.qty_on_hand = existing_qty - purchased_qty + sold_qty
            investment.qty_on_hand = existing_qty

    def _update_qty_on_purchase(self, quantity):
        self.ensure_one()
        self.qty_on_hand += quantity

    def _update_qty_on_sale(self, quantity):
        self.ensure_one()
        self.qty_on_hand -= quantity


    def create_stock_quant(self, quantity, cost_price,type,cost):
        self.ensure_one()
        if type == 'purchase':
            total_cost_price = 0.0
            total_quantity = 0.0
            lines = self.env['kg.stock.quant'].search([('investment_id', '=', self.id), ('is_purchase', '=', True)])
            for stock_quant in lines:
                total_cost_price += stock_quant.cost_price  # Summing up cost_price
                total_quantity += stock_quant.quantity  # Summing up quantity

            total_cost_price += cost_price  # Add the current cost_price
            total_quantity += quantity  # Add the current quantity

            print("total_cost_price ", total_cost_price)
            print("total_quantity ", total_quantity)


            # if stock_quant:
            #     stock_quant.write({'quantity': stock_quant.quantity + quantity,'cost_price':stock_quant.cost_price+cost_price,'avg_cost':(stock_quant.cost_price+cost_price)/ (stock_quant.quantity+ quantity ),'last_cost_price':cost_price})
            #
            # else:
                # Create new stock quant
            if lines:
                self.env['kg.stock.quant'].create({
                    'investment_id': self.id,
                    'quantity': quantity,
                    'cost_price': cost_price,
                    'price': cost,
                    'last_cost_price': quantity*cost,
                    'avg_cost': total_cost_price / total_quantity if total_quantity != 0 else 0,
                    'is_purchase':True,
                    'selling_price': ''

                })
            else:
                self.env['kg.stock.quant'].create({
                    'investment_id': self.id,
                    'quantity': quantity,
                    'cost_price': cost_price,
                    'price': cost,
                    'last_cost_price': quantity * cost,
                    'avg_cost': (quantity * cost)/quantity,
                    'is_purchase': True,
                    'selling_price':''

                })

        elif type == 'sale':
            stock_quant = self.env['kg.stock.quant'].search([('investment_id', '=', self.id),('is_sale','=',True)], limit=1)
            # if stock_quant:
            #     stock_quant.write({'quantity': stock_quant.quantity + quantity})
            #
            # else:
                # Create new stock quant
            self.env['kg.stock.quant'].create({
                'investment_id': self.id,
                'quantity': quantity,
                'price':self.face_value,
                'last_cost_price': quantity * self.face_value,
                'is_sale':True,
                'avg_cost':self.face_value,
                'selling_price':cost,
            })

    def purchase_investment(self, quantity, cost_price,type,cost):
        self.ensure_one()
        self.create_stock_quant(quantity, cost_price,type,cost)
        self._update_qty_on_purchase(quantity)

    def sale_investment(self, quantity, cost_price,type,cost):
        print("kkkkkkkkkkkkkkkkkkkkkk")
        self.ensure_one()
        self.create_stock_quant(-quantity, cost_price,type,cost)  # Negative quantity and cost_price indicate a sale
        self._update_qty_on_sale(quantity)

    def action_view_qty(self):
        return {
            'name': 'Stock Quantity',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'kg.stock.quant',
            'domain': [('id', 'in', self.kg_stock_quants.ids)],
        }

    def action_view_po(self):
        return {
            'name': 'Purchase Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'kg.purchase.order',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
        }

    def action_view_so(self):
        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'kg.sale.order',
            'domain': [('id', 'in', self.sale_order_ids.ids)],
        }

    def _compute_sale_order_ids(self):
        for record in self:
            record.sale_order_ids = self.env['kg.sale.order'].search([('investment_id', '=', record.id)])

    def _compute_purchase_order_ids(self):
        for record in self:
            record.purchase_order_ids = self.env['kg.purchase.order'].search([('investment_id', '=', record.id)])
