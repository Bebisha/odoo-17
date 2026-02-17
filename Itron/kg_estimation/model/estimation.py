#-*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date

from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_module_resource
import base64

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class SalesEstimation(models.Model):
    _name = 'sales.estimation'
    _description = 'Estimation'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _company_get(self):
        company_id = self.env['res.company']._company_default_get(self._name)
        return self.env['res.company'].browse(company_id.id)

    # @api.onchange('company_id')
    # def _onchange_company_id(self):
    #     for data in self:
    #         return {'domain':{'partner_id': ['|',('comapny_id','=',data.company_id.id),('comapny_id','=',False)]}}
    #
    name = fields.Char('Name',readonly=1)
    state = fields.Selection([('draft', 'Draft'),('requested', 'Requested'),
                              ('approve', 'Approved'),('cancel', 'Cancelled')],
                             string="State",tracking=True,default='draft')
    partner_id = fields.Many2one('res.partner',string='Customer',required=True)
    opportunity_id = fields.Many2one('crm.lead',string='Opportunity')
    user_id = fields.Many2one('res.users',string='Sales Person',
                              default=lambda self: self.env.user.id, required=True)
    approved_by = fields.Many2one('res.users',string='Approved By')
    date = fields.Date(string='Estimation Date',default=datetime.today())
    description = fields.Text(string='Note')
    order_id = fields.Many2one('sale.order', 'Order',invisible=True)
    total_cost = fields.Float(compute='_get_ttl_cost',string='TOTAL',digits=(12, 3))
    company_id = fields.Many2one('res.company', 'Company',
                                 required=True,
                                 default=_company_get,
                                 track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', 'Currency',related='company_id.currency_id')
    line_ids = fields.One2many('sales.estimation.lines','estimation_id',ondelete='cascade')
    # project_id = fields.Many2one('project.project','Project')
    project_id = fields.Many2one('project.project','Project',related='order_id.project_id')
    sales_count = fields.Integer(compute='_compute_sales_count', string="Number of Quotation")

    @api.depends('order_id')
    def _compute_sales_count(self):
        for data in self:
            rec = self.env['sale.order'].search([('estimation_id', '=', data.id)])
            data.sales_count = len(rec)

    def action_view_quotation(self):
        return {
            'name': 'Quotation',
            'domain': [('estimation_id', 'in', [self.id])],
            'context': {'search_default_estimation_id': self.id},
            'view_type': 'form',
            'view_mode': 'kanban,form,tree',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
        }

    @api.depends('line_ids.price_subtotal')
    def _get_ttl_cost(self):
        for order in self:
          amount_total = 0.0
          for line in order.line_ids:
            amount_total += line.price_subtotal
          order.update({
            'total_cost': amount_total})

    def action_request_estimation(self):
        for order in self:
            reciever = self.env.ref('sales_team.group_sale_manager')
            partners = []
            subtype_ids = self.env['mail.message.subtype'].search(
                [('res_model', '=', 'sales.estimation')]).ids
            for user in reciever.users:
                order.message_subscribe(partner_ids=[user.partner_id.id], subtype_ids=subtype_ids)
                partners.append(user.partner_id.id)
            body = _(u'New Estimation Request is raised ' + order.name + '.')
            order.message_post(body=body, partner_ids=partners)
            return order.write({'state': 'requested'})

    def action_cerate_quoation(self):
        for order in self:
            line_items = []
            for rec in order.line_ids:
                list1 = (0, 0, {
                    'product_id': rec.product_id.id,
                    'product_uom': rec.uom_id.id,
                    'name': rec.name,
                    'product_uom_qty': rec.qty,
                    'price_unit': rec.unit_cost,
                })
                line_items.append(list1)
            sale = self.env['sale.order'].create({
                'partner_id': order.partner_id.id,
                'user_id': order.user_id.id,
                'company_id': order.company_id.id,
                'order_line': line_items,
                'date_order': datetime.today(),
                'estimation_id': order.id})
            return order.write({'order_id': sale.id})

    def action_approve(self):
        for order in self:
            return order.write({'state': 'approve',
                            'approved_by': self.env.user.id})

    def action_cancel(self):
        for order in self:
            return order.write({'state': 'cancel','order_id': False,
                                })

    def button_draft(self):
        return self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('crm.estimation') or '/'
        result = super(SalesEstimation, self).create(vals)
        return result

    def unlink(self):
        for request in self:
            if request.state != 'draft':
                raise UserError(_(
                    'You cannot delete a estimation which is not draft.'
                ))
        return super(SalesEstimation, self).unlink()

class SalesEstimationLines(models.Model):
  _name = 'sales.estimation.lines'
  _description = 'Estimation Lines'

  def _compute_task(self):
        rec = self.env['project.task'].search([('estimation_line_id', '=', self.id)])
        self.task_id = rec

  product_id = fields.Many2one('product.product','Product')
  name = fields.Char('Description',related='product_id.name',readonly=0)
  uom_id = fields.Many2one('uom.uom', string='Unit',related='product_id.uom_id',readonly=False)
  qty = fields.Integer('Quantity',default=1)
  unit_cost = fields.Float('Unit Cost', digits=(12, 3),related='product_id.standard_price',readonly=False)
  price_subtotal = fields.Float('Sub Total', compute='_get_total', digits=(12, 2))
  estimation_id = fields.Many2one('sales.estimation')
  currency_id = fields.Many2one('res.currency', 'Currency', related='estimation_id.currency_id')
  company_id = fields.Many2one('res.company',related='estimation_id.company_id')
  task_id = fields.Many2one('project.task','Task',compute=_compute_task)
  effective_hours = fields.Float('Hours Spent',related='task_id.effective_hours')
  state = fields.Selection(related='estimation_id.state', string="State", tracking=True, default='draft')


  @api.depends('qty','unit_cost')
  def _get_total(self):
    for data in self:
      data.price_subtotal = data.qty * data.unit_cost


  def unlink(self):
      for request in self:
          if request.estimation_id.state != 'draft':
              raise UserError(_(
                  'You cannot delete a estimation lines which is not draft.'
              ))
      return super(SalesEstimationLines, self).unlink()