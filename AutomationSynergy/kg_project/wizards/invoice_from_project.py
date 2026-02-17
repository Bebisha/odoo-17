from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round


class ProjectInvoices(models.Model):
    _name = "invoice.project"
    _description = "Invoices from Project"

    buyer_ord_no = fields.Char()
    buyer_date = fields.Date()

    @api.model
    def default_get(self, fields):
        rec = super(ProjectInvoices, self).default_get(fields)
        product_line = []

        project = self.env['project.project'].sudo().search([
            ('id', '=', self._context.get('default_project_id'))
        ])

        sale_order = self.env['sale.order'].search([
            ('project_id', '=', project.id),
            ('project_type', '=', 'new')
        ], limit=1)  # 🔹 Fix: limit=1 avoids Expected singleton error

        inv_amount = sum(sale_order.invoice_ids.mapped('amount_total'))
        rec['sale_order_id'] = sale_order.id
        rec['currency_id'] = sale_order.currency_id.id
        rec['balance_amount'] = sale_order.amount_untaxed - inv_amount
        rec['inv_amount'] = sale_order.amount_untaxed - inv_amount
        # common_taxes = sale_order.order_line.mapped('tax_id')
        # rec['tax_id'] = [(4, 0, common_taxes.ids)]

        for item in sale_order.order_line:
            if item.product_uom_qty != 0:
                sol = item
                sol_qty = sol.product_uom_qty
                sol_del = sol.qty_delivered
                sol_wiz_qty = sol_qty - sol_del

                product_line.append((0, 0, {
                    'sale_order_line_id': item.id,
                    'name': item.name,
                    'order_partner_id': item.order_id.partner_id.id,
                    'price_unit': item.price_unit,
                    'order_id': item.order_id.id,
                    'salesman_id': item.salesman_id.id,
                    'product_uom_qty': sol_wiz_qty,
                    'price_subtotal': item.price_unit * sol_wiz_qty,
                    'product_template_id': item.product_template_id.id,
                    'qty_delivered': sol_del,
                    'qty_invoiced': item.qty_invoiced,
                }))

        rec['line_ids'] = product_line
        return rec

    @api.onchange('quotation_ids')
    def onchange_qtn(self):
        if self.quotation_ids:
            # self.invoice_variation_id = self.quotation_ids.estimation_id
            inv_amount = sum(self.quotation_ids.invoice_ids.mapped('amount_untaxed_signed'))
            self.variation_balance_amount = self.quotation_ids.amount_untaxed - inv_amount
        product_line = []
        self.variation_line_ids = False
        project = self.env['project.project'].sudo().search([('id', '=', self._context.get('default_project_id'))])
        res = {}
        sale = self.env['sale.order'].search([('project_id', '=', project.id)], order="id asc")[1:]
        res['domain'] = {'quotation_ids': [('id', 'in', sale.ids)]}
        for so in self.quotation_ids:
            for item in so.order_line:
                if item.product_uom_qty != 0:
                    sol = item
                    sol_qty = sol.product_uom_qty
                    sol_del = sol.qty_delivered
                    sol_wiz_qty = sol_qty - sol_del

                    product_line.append((0, 0, {
                        'sale_order_line_id': item.id,
                        'name': item.name,
                        'order_partner_id': item.order_id.partner_id.id,
                        'price_unit': item.price_unit,
                        'order_id': item.order_id.id,
                        'salesman_id': item.salesman_id.id,
                        'product_uom_qty': sol_wiz_qty,
                        # 'line_task_completion': item.line_task_completion,
                        'price_subtotal': item.price_unit * sol_wiz_qty,
                        'product_template_id': item.product_template_id.id,
                        'qty_delivered': sol_del,
                        'qty_invoiced': item.qty_invoiced,
                        # 'percentage_check': item.percentage_check,

                    }))

        self.variation_line_ids = product_line
        return res

    # @api.model
    # def create(self, vals):
    #     result = super(ProjectInvoices, self).create(vals)
    #     for r in range(1, len(vals.get('line_ids'))):
    #         for rec in range(2, len(vals.get('line_ids')[r])):
    #             val_in_line = vals.get('line_ids')[r][rec]
    #             val_in_line['invoice_project_wiz'] = result.id
    #             val_in_line['qty_delivered'] = result.project_id.sale_line_id.qty_delivered
    #             val_in_line['qty_invoiced'] = result.project_id.sale_line_id.qty_invoiced
    #             val_in_line['percentage_check'] = result.project_id.sale_line_id.percentage_check
    #             line_val = self.env['invoice.project.line'].create(val_in_line)
    #     return result
    #
    # def write(self, vals):
    #     res = super(ProjectInvoices, self).write(vals)
    #     for r in range(1, len(vals.get('line_ids'))):
    #         for rec in range(2, len(vals.get('line_ids')[r])):
    #             inv_proj_line_id=vals.get('line_ids')[r][1]+2
    #             val_in_line = vals.get('line_ids')[r][rec]
    #
    #             inv_perc_val=val_in_line['invoice_percentage']
    #             line=self.env['invoice.project.line'].search([('id','=',inv_proj_line_id)])
    #             line.write({'invoice_percentage':inv_perc_val})
    #
    #     return res

    line_ids = fields.Many2many('invoice.project.line', string="Invoice Lines")
    project_id = fields.Many2one('project.project', required=True)
    description = fields.Char()
    balance_amount = fields.Float()
    inv_amount = fields.Float()
    percentage_amount = fields.Float( string="Percentage amount", compute='_compute_inv_amount')
    tax_id = fields.Many2one('account.tax', string='Taxes',
                             domain=['|', ('active', '=', False), ('active', '=', True)])

    # variation
    variation_line_ids = fields.Many2many('variation.invoice.project.line', string="Invoice Lines")
    variation_ids = fields.Many2many('sale.order', compute='compute_variation_ids')
    quotation_ids = fields.Many2one('sale.order', domain="[('id', 'in', variation_ids)]")
    variation_balance_amount = fields.Float()
    variation_inv_amount = fields.Float()
    variation_percentage_amount = fields.Float(string="Percentage amount", compute='_compute_variation_percentage_amount')
    sale_order_id = fields.Many2one('sale.order')
    amount_type = fields.Selection([('fix', 'Fixed'), ('percent', 'Percentage')], default='fix', required=True)
    percent = fields.Float('Percentage')
    variation_amount_type = fields.Selection([('fix', 'Fixed'), ('percent', 'Percentage')], default='fix',
                                             required=True)
    variation_percent = fields.Float('Percentage')
    currency_id = fields.Many2one('res.currency')

    # invoice_variation_id = fields.Many2one('crm.estimation', string='Invoice Variation')

    @api.depends('amount_type', 'percent', 'balance_amount')
    def _compute_inv_amount(self):
        for rec in self:
            if rec.amount_type == 'percent':
                rec.percentage_amount = (rec.balance_amount * rec.percent) / 100 if rec.balance_amount else 0.0
            else:
                rec.percentage_amount =0.0

    @api.depends('variation_amount_type', 'variation_percent', 'variation_balance_amount')
    def _compute_variation_percentage_amount(self):
        for rec in self:
            if rec.variation_amount_type == 'percent':
                rec.variation_percentage_amount = (rec.variation_balance_amount * rec.variation_percent) / 100 if rec.variation_balance_amount else 0.0
            else:
                rec.variation_percentage_amount = 0.0

    @api.depends('project_id')
    def compute_variation_ids(self):
        for rec in self:
            sale_order = self.env['sale.order'].search(
                [('project_id', '=', rec.project_id.id), ('state', 'in', ['done', 'sale']),
                 ('project_type', '!=', 'new')])
            rec.variation_ids = False
            # sale_ids = []
            # for order_name in sale_order:
            #     if order_name.name[-1].isalpha():  # Check if the last character is a letter
            #
            #         sale_ids.append(order_name.id)

            rec.variation_ids = [(6, 0, sale_order.ids)]

    def _prepare_invoice_line(self):
        self.ensure_one()

        today = date.today()

        invoice_vals = {
            'ref': self.sale_order_id.name,
            'move_type': 'out_invoice',
            'currency_id': self.sale_order_id.currency_id.id,
            'partner_id': self.sale_order_id.partner_id.id,
            'user_id': self.sale_order_id.user_id.id,
            'invoice_user_id': self.sale_order_id.user_id.id,
            'invoice_origin': self.sale_order_id.name,
            'company_id': self.project_id.company_id.id,
            'invoice_date': today,
            'buyer_ord_no': self.buyer_ord_no,
            'buyer_date': self.buyer_date,
            'project_id': self.project_id.id,
            # 'estimation_id': self.project_id.estimation_id.id,
            'sale_order_id': self.sale_order_id.id,
        }
        invoice_line_ids = []
        amount = self[0].inv_amount
        taxls = []
        if self.tax_id:
            taxls.append(self.tax_id.id)
        acc = self.project_id.analytic_account_id.id
        invoice_line_ids.append((0, 0, {
            'quantity': 1,
            'price_unit': amount,
            'name': self.description,
            'tax_ids': [(6, 0, taxls)],
            # 'analytic_distribution': {acc: 100},
        })),
        invoice_vals['invoice_line_ids'] = invoice_line_ids
        return invoice_vals

    def _prepare_variation_invoice_line(self):
        self.ensure_one()
        today = date.today()
        invoice_vals = {
            'ref': self.quotation_ids.name,
            'move_type': 'out_invoice',
            'currency_id': self.quotation_ids.currency_id.id,
            'partner_id': self.quotation_ids.partner_id.id,
            'user_id': self.quotation_ids.user_id.id,
            'invoice_user_id': self.quotation_ids.user_id.id,
            'invoice_origin': self.quotation_ids.name,
            'company_id': self.quotation_ids.company_id.id,
            'invoice_date': today,
            'buyer_ord_no': self.buyer_ord_no,
            'buyer_date': self.buyer_date,
            'project_id': self.project_id.id,
            'sale_order_id': self.quotation_ids.id,

            # 'estimation_id': self.quotation_ids.estimation_id.id,
            # 'estimation_id': self.quotation_ids.estimation_id.id,

        }
        invoice_line_ids = []
        amount = self[0].variation_inv_amount
        taxls = []
        if self.tax_id:
            taxls.append(self.tax_id.id)
        acc = self.project_id.analytic_account_id.id
        invoice_line_ids.append((0, 0, {
            'quantity': 1,
            'price_unit': amount,
            'name': self.description,
            'tax_ids': [(6, 0, taxls)],
            # 'analytic_distribution': {acc: 100},
            # 'var_ref': self.quotation_ids.id,

        })),
        invoice_vals['invoice_line_ids'] = invoice_line_ids
        return invoice_vals

    def create_variation_project_invoice(self):
        if not self.quotation_ids:
            raise ValidationError(_('Please select a quotation.'))
        if self.variation_amount_type == 'percent':
            if self.variation_percent > 100:
                raise ValidationError(_('Percentage should be lesser than 100'))
            elif self.variation_percent == 0:
                raise ValidationError(_('Percentage should be greater than zero'))
            self.variation_inv_amount = (self.variation_percent * self.variation_balance_amount) / 100

        if self.variation_inv_amount <= 0:
            raise ValidationError(_('Invoice Amount should be greater than zero'))
        if float_round(self.variation_inv_amount, 2) > float_round(self.variation_balance_amount, 2):
            raise ValidationError(_('Invoice Amount should not exceed balance amount...'))
        invoice_vals = self._prepare_variation_invoice_line()
        inv_moves = self.env['account.move'].create(invoice_vals)
        inv_moves.action_post()
        self.quotation_ids.update({'invoice_ids': [(4, inv_moves.id)]})
        line_id = inv_moves.invoice_line_ids[0].id
        for line in self.quotation_ids.order_line:
            line.update({'invoice_lines': [(4, line_id)]})

    def create_project_invoice(self):
        # wiz_line = self.env['invoice.project.line'].search([('invoice_project_wiz', '=', self.id)])
        if self.amount_type == 'percent':
            if self.percent > 100:
                raise ValidationError(_('Percentage should be lesser than 100'))
            elif self.percent == 0:
                raise ValidationError(_('Percentage should be greater than zero'))
            self.inv_amount = (self.percent * self.balance_amount) / 100
        # for wiz in wiz_line:
        # per_val = 0
        # per_val += wiz.invoice_percentage
        # cheked_val = per_val + wiz.sale_order_line_id.percentage_check
        # if cheked_val  > wiz.line_task_completion:
        #     raise ValidationError(_('Invoice Upto task completed '))
        # else:
        #     wiz.sale_order_line_id.write({'percentage_check':cheked_val })
        if self.inv_amount <= 0:
            raise ValidationError(_('Invoice Amount should be greater than zero'))
        # if self.tax_id:
        #     inv_amount = self[0].inv_amount
        #     tax = self.tax_id.compute_all(inv_amount, quantity=1, product=False,
        #                                   partner=False)['taxes']
        #     amount = inv_amount + tax[0]['amount']
        #     if amount > self.balance_amount:
        #         raise ValidationError(_('Invoice Amount with tax should not exceed balance amount...'))
        # else:
        if float_round(self.inv_amount, 2) > float_round(self.balance_amount, 2):
            raise ValidationError(_('Invoice Amount should not exceed balance amount...'))
        invoice_vals = self._prepare_invoice_line()
        inv_moves = self.env['account.move'].create(invoice_vals)
        inv_moves.action_post()
        sale = self.sale_order_id
        sale.update({'invoice_ids': [(4, inv_moves.id)]})
        line_id = inv_moves.invoice_line_ids[0].id
        for line in sale.order_line:
            line.update({'invoice_lines': [(4, line_id)]})

        # wiz_line = self.env['invoice.project.line'].search([('invoice_project_wiz', '=', self.id)])
        # for l in wiz_line:
        #     l.write({'invoice_id': inv_moves.id})
        # sale_order = self.env['sale.order'].search([('id', '=', inv_moves.sale_order_id.id)])
        # for order in sale_order:
        #     invoices_inv = self.env['account.move'].sudo().search(
        #         [('sale_order_id', '=', order.project_id.sale_order_id.id)])
        #     sale_ord_lin_inv = self.env['sale.order.line'].search(
        #         [('invoice_lines', '=', invoices_inv.invoice_line_ids.ids)])
        #     invoices = sale_ord_lin_inv.invoice_lines.move_id.filtered(
        #         lambda r: r.move_type in ('out_invoice'))
        #
        #     order.invoice_ids = invoices
        #
        #     order.invoice_count = len(invoices)
        #
        #
        # wiz_inv_line = self.env['invoice.project.line'].search([('invoice_id', '=', inv_moves.id)])
        #
        # for w in wiz_inv_line:
        #     # w.write({'percentage_check':w.invoice_percentage
        #     #                 })
        #     sale_line = self.env['sale.order.line'].search([('id', '=', w.sale_order_line_id.id)])
        #     for line in sale_line:
        #
        #
        #         line.write({'qty_delivered': sum(t.quantity for t in line.invoice_lines),
        #                     'qty_invoiced': sum(t.quantity for t in line.invoice_lines),
        #                     # 'percentage_check': sum(t.invoice_percentage for t in line.invoice_lines),
        #                     })

        # inv_moves.action_post()


class ProjectInvoicesLine(models.Model):
    _name = "invoice.project.line"
    _description = "Invoices from Project Line"

    invoice_id = fields.Many2one('account.move', string="Invoice")
    invoice_project_wiz = fields.Many2one('invoice.project', string="inn")
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sales Order Line", store=True)
    order_id = fields.Many2one(comodel_name='sale.order', string="Order Reference", store=True)
    order_partner_id = fields.Many2one('res.partner', string="Customer", store=True)
    name = fields.Text(string="Description", store=True)
    salesman_id = fields.Many2one('res.partner', string="Salesperson", store=True)
    product_uom_qty = fields.Float(string="Quantity", default=1.0, store=True)
    price_unit = fields.Float(string="Unit Price", store=True)
    line_task_completion = fields.Float("Task Status", store=True)
    price_subtotal = fields.Monetary(string="Subtotal", store=True)
    currency_id = fields.Many2one('res.currency', store=True)
    invoice_percentage = fields.Float(string="Invoice Percentage", store=True)
    product_template_id = fields.Many2one('product.template', string="Product Template", store=True)
    qty_delivered = fields.Float(string="Delivered Quantity", store=True)
    qty_invoiced = fields.Float(string="Invoiced Quantity", store=True)
    # percentage_check = fields.Float(string=" Percentage Check", compute='compute_percentage_check',store=True)
    percentage_check = fields.Float(string="Invoiced Percentage", store=True)

    # @api.depends('percentage_check','invoice_percentage')
    # def compute_percentage_check(self):
    #     per_val = 0
    #     for val in self:
    #
    #             # if val.invoice_percentage !=0.0:
    #
    #             per_val += val.invoice_percentage
    #     self.percentage_check = per_val

    # if val.invoice_percentage > val.percentage_check:
    #     raise ValidationError(_('Invoice Upto task completed '))

    @api.onchange('percentage_check')
    def onchange_invoice_percentage(self):
        for inv in self:
            if inv.percentage_check > inv.line_task_completion:
                raise ValidationError(_('Amount Exceeded...'))


class ProjectInvoicesLine(models.Model):
    _name = "variation.invoice.project.line"
    _description = "Invoices from Project Line"

    invoice_id = fields.Many2one('account.move', string="Invoice")
    invoice_project_wiz = fields.Many2one('invoice.project', string="inn")
    sale_order_line_id = fields.Many2one('sale.order.line', string="Sales Order Line", store=True)
    order_id = fields.Many2one(comodel_name='sale.order', string="Order Reference", store=True)
    order_partner_id = fields.Many2one('res.partner', string="Customer", store=True)
    name = fields.Text(string="Description", store=True)
    salesman_id = fields.Many2one('res.partner', string="Salesperson", store=True)
    product_uom_qty = fields.Float(string="Quantity", default=1.0, store=True)
    price_unit = fields.Float(string="Unit Price", store=True)
    line_task_completion = fields.Float("Task Status", store=True)
    price_subtotal = fields.Monetary(string="Subtotal", store=True)
    currency_id = fields.Many2one('res.currency', store=True)
    invoice_percentage = fields.Float(string="Invoice Percentage", store=True)
    product_template_id = fields.Many2one('product.template', string="Product Template", store=True)
    qty_delivered = fields.Float(string="Delivered Quantity", store=True)
    qty_invoiced = fields.Float(string="Invoiced Quantity", store=True)
    # percentage_check = fields.Float(string=" Percentage Check", compute='compute_percentage_check',store=True)
    percentage_check = fields.Float(string="Invoiced Percentage", store=True)

    # @api.depends('percentage_check','invoice_percentage')
    # def compute_percentage_check(self):
    #     per_val = 0
    #     for val in self:
    #
    #             # if val.invoice_percentage !=0.0:
    #
    #             per_val += val.invoice_percentage
    #     self.percentage_check = per_val

    # if val.invoice_percentage > val.percentage_check:
    #     raise ValidationError(_('Invoice Upto task completed '))

    @api.onchange('percentage_check')
    def onchange_invoice_percentage(self):
        for inv in self:
            if inv.percentage_check > inv.line_task_completion:
                raise ValidationError(_('Amount Exceeded...'))
