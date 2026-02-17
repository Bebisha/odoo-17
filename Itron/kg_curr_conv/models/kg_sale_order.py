# -*- coding: utf-8 -*-
from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_short_name = fields.Char('Partner Short Name', related='partner_id.name', store=True, readonly=True)
    industry_id = fields.Many2one('kg.industry')
    # @api.model
    @api.depends('kg_invoice_ids.amount_residual','kg_invoice_ids.net_total', 'amount_total', 'kg_un_invoiced_amt_local')
    def _get_total_invoiced(self):

        for order in self:
            invoice_ids = order.invoice_ids
            total_value = order.amount_total

            total_invoiced = 0
            kg_total_received = 0
            kg_tds_amount = 0

            for inv in invoice_ids:
                if inv.state not in ('draft', 'cancel'):
                    if order.currency_id:
                        total_invoiced = total_invoiced + order.currency_id._convert((inv.net_total), order.currency_id,
                                                                                    order.company_id, order.date_order
                                                                                    )

                        kg_tds_amount = kg_tds_amount + order.currency_id._convert((inv.kg_tds_amount),
                                                                                            order.currency_id,
                                                                                            order.company_id,
                                                                                            order.date_order
                                                                                            )

                        kg_total_received = kg_total_received + order.currency_id._convert((inv.net_total - inv.amount_residual),
                                                                                          order.currency_id,
                                                                                          order.company_id,
                                                                                          order.date_order
                                                                                          )
            order.kg_total_invoiced = total_invoiced
            order.kg_total_received = kg_total_received
            kg_pending_amt = (total_invoiced - kg_total_received)
            order.kg_tds_amt = kg_tds_amount
            order.kg_pending_amt = kg_pending_amt
            kg_un_invoiced_amt = total_value + kg_tds_amount - total_invoiced
            order.kg_un_invoiced_amt = kg_un_invoiced_amt

            if order.kg_paid is True:
                order.kg_un_invoiced_amt = 0

            kg_total_invoiced_local = 0.0
            kg_total_received_local = 0.0
            kg_un_invoiced_amt_local = 0.0
            kg_pending_amt_local = 0.0
            kg_tds_amt_local = 0.0

            ctx = {}
            ctx['date'] = order.date_order
            if order.currency_id:

                kg_total_invoiced_local = order.currency_id._convert(total_invoiced,order.company_id.currency_id,
                                                                            order.company_id,order.date_order
                                                                            )
                kg_total_received_local = order.currency_id._convert(kg_total_received, order.company_id.currency_id,
                                                                            order.company_id, order.date_order
                                                                            )
                kg_pending_amt_local = order.currency_id._convert(kg_pending_amt, order.company_id.currency_id,
                                                                            order.company_id, order.date_order
                                                                            )
                kg_un_invoiced_amt_local = order.currency_id._convert(kg_un_invoiced_amt, order.company_id.currency_id,
                                                                         order.company_id, order.date_order
                                                                         )
                kg_tds_amt_local = order.currency_id._convert(kg_tds_amount, order.company_id.currency_id,
                                                                             order.company_id, order.date_order
                                                                             )
            order.kg_total_invoiced_local = kg_total_invoiced_local or 0.0
            order.kg_total_received_local = kg_total_received_local or 0.0
            order.kg_pending_amt_local = kg_pending_amt_local or 0.0
            order.kg_un_invoiced_amt_local = kg_un_invoiced_amt_local or 0.0
            order.kg_tds_amt_local = kg_tds_amt_local or 0.0


    ### Search for computed field
    @api.model
    def search_total_invoiced(self, operator, value):
        recs = self.search([])
        ids = []
        for i in recs:
            if operator == '=':
                if value is False:
                    if not i.kg_total_invoiced:
                        ids.append(i.id)
                elif i.kg_total_invoiced == value:
                    ids.append(i.id)
            if operator == '!=':
                if value is False:
                    if i.kg_total_invoiced:
                        ids.append(i.id)
                elif i.kg_total_invoiced != value:
                    ids.append(i.id)
            if operator == '>':
                if i.kg_total_invoiced > value:
                    ids.append(i.id)
            if operator == '>=':
                if i.kg_total_invoiced >= value:
                    ids.append(i.id)
            if operator == '<':
                if i.kg_total_invoiced < value:
                    ids.append(i.id)
            if operator == '<=':
                if i.kg_total_invoiced <= value:
                    ids.append(i.id)

        if ids:
            return [('id', 'in', ids)]

    check_invoice = fields.Boolean(compute="_display_discount_col")

    def _prepare_confirmation_values(self):
        """ Prepare the sales order confirmation values.

        Note: self can contain multiple records.

        :return: Sales Order confirmation values
        :rtype: dict
        """
        return {
            'state': 'sale',
            'date_order': fields.Datetime.now() if not self.date_order else self.date_order
        }

    @api.depends('kg_un_invoiced_amt_local')
    def _display_discount_col(self):
        for data in self:
            if data.kg_un_invoiced_amt_local <= 0:
                data.check_invoice = True
            else:
                data.check_invoice = False

    local_curr_val = fields.Float('Company(Cur)', compute="convert_curr", store=True)
    company_currency_id = fields.Many2one('res.currency', 'Currency', compute="know_curr")

    kg_total_invoiced = fields.Float(string='Total Invoiced', store=True, readonly=True, compute='_get_total_invoiced')
    kg_total_invoiced_local = fields.Float('Total Invoiced Company(Cur)', store=True, readonly=True,
                                           compute='_get_total_invoiced')

    kg_total_received = fields.Float('Total Received', store=True, readonly=True, compute='_get_total_invoiced')
    kg_total_received_local = fields.Float('Total Received Company(Cur)', store=True, readonly=True,
                                           compute='_get_total_invoiced')


    kg_pending_amt = fields.Float('Pending Amount', store=True, readonly=True, compute='_get_total_invoiced')
    kg_pending_amt_local = fields.Float('Pending Amount Company(Cur)', store=True, readonly=True,
                                        compute='_get_total_invoiced')
    kg_tds_amt = fields.Float('TDS Amount', store=True, readonly=True, compute='_get_total_invoiced')
    kg_tds_amt_local = fields.Float('TDS Amount Company(Cur)', store=True, readonly=True,
                                            compute='_get_total_invoiced')

    kg_un_invoiced_amt = fields.Float('Uninvoiced Amount', store=True, readonly=True, compute='_get_total_invoiced')
    kg_un_invoiced_amt_local = fields.Float('Uninvoiced Amount Company(Cur)', store=True, readonly=True,
                                            compute='_get_total_invoiced')

    kg_invoice_ids = fields.One2many("account.move", 'kg_sale_order_id', 'Invoices')

    project_id = fields.Many2one('project.project', 'Analytic Account',
                                 states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                 help="The analytic account related to a sales order.", copy=False,)

    kg_paid = fields.Boolean('Paid', default=False)
    kg_lpo = fields.Char(string="LPO Reference")
    invoice_percent = fields.Float(compute='_invoice_percentage', string="Invoice %")

    @api.depends('kg_total_invoiced_local','local_curr_val')
    @api.model
    def _invoice_percentage(self):
        for record in self:
            if record.local_curr_val !=0:
                percentage = (record.kg_total_invoiced_local /(record.local_curr_val + record.kg_tds_amt_local))* 100
                record.invoice_percent = percentage
            else:
                record.invoice_percent = 0

    @api.depends('company_id')
    def know_curr(self):
        for record in self:
            currency = record.company_id.currency_id
            record.company_currency_id = currency.id

    @api.depends('amount_total', 'pricelist_id')
    def convert_curr(self):
        for record in self:
            new_val = 0.0
            context = dict(self._context or {})
            ctx = context.copy()
            ctx['date'] = record.date_order
            if record.currency_id:
                new_val = record.pricelist_id.currency_id._convert(record.amount_total,record.company_id.currency_id, record.company_id,
                                                           record.date_order)
            record.local_curr_val = new_val or 0.0

    def create_project(self):
        for data in self:
            vals = {'partner_id': data.partner_id.id,
                    'user_id': data.user_id.id,
                    'name': data.name,}
            rec = self.env['project.project'].create(vals)
            data.project_id = rec.id
            data.write({'project_id': rec.id,})
            return

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['kg_lpo'] = self.kg_lpo
        return invoice_vals
