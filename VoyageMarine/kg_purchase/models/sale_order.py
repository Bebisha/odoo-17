from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_warning = fields.Boolean(string="Warning", copy=False)
    is_bocking = fields.Boolean(string="Blocking", copy=False)
    po_created = fields.Boolean(string="IS PO Create", copy=False)



    @api.model
    def create(self, vals):
        credit_limit_action = self.env['ir.config_parameter'].sudo().get_param(
            'kg_purchase.account_credit_limit_action'
        )
        if credit_limit_action == 'warning':
            vals['is_warning'] = True

        elif credit_limit_action == 'blocking':
            vals['is_bocking'] = True
            raise ValidationError(_("You cannot exceed the credit limit!"))
        else:
            vals['is_warning'] = False
            vals['is_bocking'] = False

        return super(SaleOrder, self).create(vals)

    def action_create_rfq(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create RFQ'),
            'res_model': 'create.purchaseorder',
            'view_mode': 'form',
            'view_id': self.env.ref('kg_purchase.view_transientmodel_wizard_form').id,
            'target': 'new',
            'context': {
                'active_ids': self.ids,
            }
        }

    def action_open_rfq_order(self):
        return {
            'name': 'Purchase Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.rfq_ids.ids),('state', '!=', 'purchase')],
            'target': 'current',
            'context': {'create': False}
        }

    def action_open_purchase_order(self):
        return {
            'name': 'Purchase Orders',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.po_ids.ids), ('state', '=', 'purchase')],
            'target': 'current',
            'context': {'create': False}
        }

    def _get_po(self):
        for rec in self:
            purchase_ids = rec.est_po_ids.filtered(lambda po: po.state == 'purchase') | \
                           rec.enq_po_ids.filtered(lambda po: po.state == 'purchase') | \
                           rec.mr_po_ids.filtered(lambda po: po.state == 'purchase') | \
                           rec.so_po_ids.filtered(lambda po: po.state == 'purchase')
            rec.po_ids = purchase_ids
            rec.po_count = len(rec.po_ids)


    def _get_rfq(self):
        for rec in self:
            print(rec.est_po_ids,"est_po_ids")
            print(rec.enq_po_ids,"enq_po_ids")
            draft_rfq_ids = rec.est_po_ids.filtered(lambda po: po.state != 'purchase') | \
                            rec.enq_po_ids.filtered(lambda po: po.state != 'purchase') | \
                            rec.mr_po_ids.filtered(lambda po: po.state != 'purchase') | \
                            rec.so_po_ids.filtered(lambda po: po.state != 'purchase')
            print(draft_rfq_ids,"draft_rfq_ids")
            rec.rfq_ids = draft_rfq_ids
            rec.rfq_count = len(rec.rfq_ids)



    po_count = fields.Integer(compute='_get_po', string='Purchase')
    rfq_count = fields.Integer(compute='_get_rfq', string='RFQ')

    def action_confirm(self):
        for order in self:
            if order.partner_id.state != 'approval':
                raise UserError('Customer must be approved to confirm the sales order.')
        return super(SaleOrder, self).action_confirm()

    duration_validity = fields.Char(string="Delivery Duration" ,compute="_compute_expiration_date")

    @api.depends('validity_date')
    def _compute_expiration_date(self):
        for order in self:
            if order.validity_date:
                validity_date = fields.Date.from_string(order.validity_date)
                current_date = fields.Date.today()
                delta = relativedelta(validity_date, current_date)
                if delta.years == 0 and delta.months == 0:
                    order.duration_validity = f"{delta.days} days"
                elif delta.years == 0:
                    order.duration_validity = f"{delta.months} months"
                else:
                    order.duration_validity = f"{delta.years} years"
            else:
                order.duration_validity = "0 days"



    # @api.depends('company_id', 'partner_id', 'amount_total')
    # def _compute_partner_credit_warning(self):
    #     for order in self:
    #         order.with_company(order.company_id)
    #         order.partner_credit_warning = ''
    #         show_warning = order.state in ('draft', 'sent') and \
    #                        order.company_id.account_use_credit_limit
    #         if show_warning and self.is_warning == True:
    #             order.partner_credit_warning = self.env['account.move']._build_credit_warning_message(
    #                 order,
    #                 current_amount=(order.amount_total / order.currency_rate),
    #             )
    #         if self.is_bocking == True :
    #             raise ValidationError(_("You cannot exceed credit limit ! "))


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    po_qty = fields.Float(string="PO Qty", copy=False)
    balance_qty = fields.Float(string='Balance Quantity', compute='_compute_balance_qty', store=True)
    is_subitem = fields.Boolean(default=False)

    @api.onchange('name')
    def caps_name(self):
        if self.name:
            self.name = str(self.name).capitalize()

    @api.depends('product_uom_qty', 'po_qty')
    def _compute_balance_qty(self):
        for line in self:
            line.balance_qty = line.product_uom_qty - line.po_qty

    is_price_update = fields.Boolean(default=False, compute="compute_is_price_update")

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
                continue
            if not line.product_uom or not line.product_id:
                line.price_unit = 0.0
            else:
                if line.is_price_update:
                    line.price_unit = line.price_unit
                else:
                    line = line.with_company(line.company_id)
                    price = line._get_display_price()
                    line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
                        price,
                        line.currency_id or line.order_id.currency_id,
                        product_taxes=line.product_id.taxes_id.filtered(
                            lambda tax: tax.company_id == line.env.company
                        ),
                        fiscal_position=line.order_id.fiscal_position_id,
                    )

    @api.depends('price_unit')
    def compute_is_price_update(self):
        for rec in self:
            if rec.price_unit:
                rec.is_price_update = True
            else:
                rec.is_price_update = False

