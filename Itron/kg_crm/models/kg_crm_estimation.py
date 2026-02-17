import base64
from datetime import datetime

import xlsxwriter
from six import BytesIO
from odoo.exceptions import UserError, AccessError

from odoo import fields, models, api


class KgCrmEstimation(models.Model):
    _name = 'kg.crm.estimation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'CRM Estimation'

    name = fields.Char("Name")
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    date = fields.Date('Date')
    scope_of_work = fields.Text(string="Scope of Work")
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    total = fields.Monetary(string='Total',compute='_compute_total', store=True, currency_field='currency_id')
    margin = fields.Float(string='Margin')
    margin_amount = fields.Monetary(string='Margin Amount',compute='_compute_margin_amount', store=True, currency_field='currency_id')
    proposal_cost = fields.Monetary(string='Proposal Cost', compute='_compute_proposal_cost', store=True, currency_field='currency_id')
    lead_id = fields.Many2one('crm.lead', string="Lead", ondelete='cascade')
    estimation_line_ids = fields.One2many('kg.crm.estimation.line', 'estimation_id')
    is_confirmed = fields.Boolean(string='Is Confirmed', default=False)
    quotation_ids = fields.One2many('sale.order', 'crm_estimation_id', string='Quotations')
    quotation_count = fields.Integer(string='Quotations Count', compute='_compute_quotation_count')

    def _compute_quotation_count(self):
        for record in self:
            record.quotation_count = len(record.quotation_ids)

    @api.depends('estimation_line_ids.cost')
    def _compute_total(self):
        for estimation in self:
            estimation.total = sum(line.cost for line in estimation.estimation_line_ids)

    @api.depends('total', 'margin')
    def _compute_margin_amount(self):
        for estimation in self:
            estimation.margin_amount = estimation.total * (estimation.margin)

    @api.depends('total', 'margin_amount')
    def _compute_proposal_cost(self):
        for estimation in self:
            estimation.proposal_cost = estimation.total + estimation.margin_amount

    def button_confirm(self):
        self.write({'is_confirmed': True})
        return {'type': 'ir.actions.act_window_close'}

    def create_quotation(self):
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']

        for estimation in self:
            if not estimation.estimation_line_ids:
                raise UserError('No estimation lines to create a quotation.')

            sale_order = SaleOrder.create({
                'crm_estimation_id': estimation.id,
                'partner_id': estimation.customer_id.id,
                'date_order': fields.Datetime.now(),
                'origin': estimation.name,
                'note': estimation.scope_of_work,
            })
            for line in estimation.estimation_line_ids:
                SaleOrderLine.create({
                    'order_id': sale_order.id,
                    'product_id': line.item_id.id,
                    'product_uom_qty': 1,
                    'name': line.item_id.name,
                    'price_unit': line.cost,
                })

            return {
                'type': 'ir.actions.act_window',
                'name': 'Quotation',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': sale_order.id,
                'target': 'current',
            }
        return True

    def action_view_quotations(self):
        self.ensure_one()
        return {
            'name': 'Quotations',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('crm_estimation_id', '=', self.id)],
        }

class CrmEstimationLine(models.Model):
    _name = 'kg.crm.estimation.line'
    _description = 'CRM Estimation Line'
    _rec_name = 'item_id'

    item_id = fields.Many2one('product.product',string="Item", required=True)
    effort = fields.Float(string="Effort (In Week)")
    cost= fields.Monetary(string='Cost', compute='_compute_cost', store=True, currency_field='currency_id')
    estimation_id = fields.Many2one('kg.crm.estimation')
    currency_id = fields.Many2one('res.currency', related='estimation_id.currency_id', store=True, readonly=True)

    @api.depends('effort')
    def _compute_cost(self):
        config_param_rec = self.env['ir.config_parameter'].sudo()
        per_weak_cost = float(config_param_rec.get_param('kg_crm.per_weak_cost', default=0.0))
        for line in self:
            if per_weak_cost != 0:
                line.cost = per_weak_cost * line.effort
            else:
                line.cost = line.effort


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    crm_estimation_id = fields.Many2one('kg.crm.estimation', string='Estimation')
