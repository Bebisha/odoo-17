# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    bank_id = fields.Many2one('account.journal','Bank')
    partner_short_name = fields.Char('Partner Short Name', related='partner_id.name', store=True, readonly=True)
    pi_number = fields.Char('Proforma Number')
    kg_lpo = fields.Char(string="LPO Reference", readonly=False,store=True)

    # state = fields.Selection(selection_add=[
    #     ('proforma', 'Proforma')], ondelete={'proforma': 'cascade'})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Proforma'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
    vou_inv_number = fields.Char(string='Invoice Number', copy=False)
    vou_invoice_date = fields.Date(string='Invoice Date', copy=False)
    vou_due_date = fields.Date(string='Due Date', copy=False)
    country_code = fields.Char(string='Country Code', related='company_id.country_code')

    def action_proforma(self):
        self.state = 'proforma'
        
    def action_draft(self):
        self.state = 'draft'

    def action_invoice_print(self):
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))

        self.filtered(lambda inv: not inv.is_move_sent).write({'is_move_sent': True})
        if self.user_has_groups('account.group_account_invoice'):
            return self.env.ref('kg_curr_conv.kg_print_and_send_invoice').report_action(self)
        else:
            return self.env.ref('account.account_invoices_without_payment').report_action(self)


    total_local = fields.Float('Total(Company Currency)', compute="convert_curr", store=True)
    amount_total = fields.Float('Total', compute="convert_curr", store=True)
    due_local = fields.Float('Amount Due(Company Currency)', compute="convert_curr", store=True)
    company_currency_id1 = fields.Integer('Currency', compute="know_curr")
    kg_sale_order_id = fields.Many2one('sale.order', string="Sale Order")

    project_id = fields.Many2one('project.project', 'Project',related='kg_sale_order_id.project_id')
    apply_tds = fields.Boolean('Apply TDS',default=False)
    tds_tax_id = fields.Many2one('account.tax','TDS %', domain="[('is_tds', '=', True)]")
    kg_tds_account_id = fields.Many2one('account.account', string="TDS Account",related='tds_tax_id.tds_account_id',readonly=True)
    kg_tds_percentage = fields.Float(string="TDS %")
    kg_tds_amount = fields.Float(string="TDS Amount",compute='onchange_update_tds')
    kg_total_amount = fields.Float(string="TDS Tax",compute='onchange_update_tds')
    net_total = fields.Float(string="Net Total",compute='onchange_update_tds')
    tds_check = fields.Boolean('Check',default=False, copy=False)

    # def finalize_invoice_move_lines(self, move_lines):
        # company_id = self.company_id and self.company_id.id
        # result = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        #
        # if company_id in (3, 6) and self.type == 'out_invoice':
        #     kg_tds_account_id = self.kg_tds_account_id and self.kg_tds_account_id.id or False
        #     if not kg_tds_account_id:
        #         raise UserError(_('Tds Account not defined'))
        #
        #     for line in result:
        #         account_id = line[2]['account_id']
        #         account_obj = self.env['account.account'].browse(account_id)
        #         user_type_id = account_obj.user_type_id and account_obj.user_type_id.name
        #         if line[2]['debit'] and user_type_id == 'Receivable':
        #             line[2]['debit'] = line[2]['debit'] - self.kg_tds_amount
        #             val = (0, 0, {'analytic_account_id': line[2]['analytic_account_id'], 'name': 'TDS Re>
        #                                                                                          'product_uom_id'
        #                    : line[2]['product_uom_id'], 'invoice_id': line[2]['in>
        #                    'currency_id': line[2]['currency_id'], 'credit': line[2]['credit'],
        #                    'product_id': line[2]['product_id'], 'date_maturity': line[2]['date_ma>
        #                    'debit': self.kg_tds_amount, 'amount_currency': line[2]['amount_curren>
        #                    'quantity': line[2]['quantity'], 'partner_id': line[2]['partner_id'],
        #                    'account_id': kg_tds_account_id})
        #             result.append(val)
        # return result

    #
    # kg_tds_amount = fields.Float(string="TDS Amount")
    # kg_tds_account_id = fields.Many2one('account.account', string="TDS Account")

    # @api.onchange('amount_total', 'kg_tds_percentage')
    # def onchange_update_tds(self):
    #
    #     self.kg_tds_amount = float(self.kg_tds_percentage / 100) * self.amount_untaxed

    # tds_move = fields.Many2one('account.move.line')
    @api.model
    @api.depends('amount_total','tds_tax_id')
    def onchange_update_tds(self):
        kg_tds_amount = 0
        # amount_total = 0
        for data in self:
            if data.apply_tds:
                kg_tds_amount = float(data.tds_tax_id.amount / 100) * (data.amount_untaxed)
                data.kg_tds_amount = kg_tds_amount
                data.net_total = data.amount_untaxed + data.amount_tax + kg_tds_amount
            else:
                data.kg_tds_amount = 0
                data.net_total = data.amount_untaxed + data.amount_tax

    # def _check_balanced(self, container):
    #     return True


    # @api.depends('kg_tds_amount')
    # def action_post(self):
    #     # result = super(AccountInvoice, self).write(vals)
    #     for data in self:
    #         if data.apply_tds and data.kg_tds_account_id != False:
    #             # invoice_line_ids = self.invoice_line_ids.ids
    #             tds_charges = {
    #                 'sequence': False,
    #                 'name': 'TDS Receivable',
    #                 'account_id': data.kg_tds_account_id.id,
    #                 'quantity': 1,
    #                 'discount': 0,
    #                 'tax_ids': [(6, 0, [])],
    #                 'analytic_tag_ids': [(6, 0, [])],
    #                 'price_unit': data.kg_tds_amount,
    #                 'currency_id': data.currency_id.id,
    #                 'move_id': data.id
    #             }
    #             print(tds_charges)
    #             move_line_id = self.env['account.move.line'].create(tds_charges)
    #             data._onchange_invoice_line_ids()
    #             data.tds_check = True
    #         return super(AccountInvoice, self).action_post()

    def update_tds(self, tds_line, receivable_line):
        if tds_line and receivable_line:
            tds_line.debit = self.kg_tds_amount
            receivable_line.debit = receivable_line.debit - self.kg_tds_amount


    def action_post(self):
        res = super(AccountInvoice, self).action_post()
        if self.apply_tds and self.kg_tds_account_id != False:
            if self.move_type == 'out_invoice':
                for line in self.line_ids:
                    user_type_id = line.account_id.account_type
                    if line.debit and user_type_id == 'asset_receivable':
                        vals = {'account_id': self.kg_tds_account_id.id,
                                'partner_id': self.partner_id.id,
                                'name': 'TDS Receivable',
                                'currency_id': self.currency_id.id,
                                'amount_currency': self.kg_tds_amount,
                                'display_type': 'tax',
                                'move_id': self.id}
                        self.env['account.move.line'].create(vals)
                    self.tds_check = True
        return res


    @api.model
    def create(self, values):
        result = super(AccountInvoice, self).create(values)
        origin = result.invoice_origin
        if origin:
            sale_oder_obj = self.env['sale.order'].search([('name', '=', origin), ('company_id', '=', self.env.company.id)])
            result.kg_sale_order_id = sale_oder_obj and sale_oder_obj.id or False
            result.project_id = sale_oder_obj.project_id and sale_oder_obj.project_id.id or False
        return result


    @api.depends('company_id')
    def know_curr(self):
        for record in self:
            print (record.env.context, '111111111', record.env.user.company_id.name)
            currency = record.env.user.company_id.currency_id

            record.company_currency_id1 = currency.id

    @api.depends('amount_total', 'currency_id', 'amount_residual')
    def convert_curr(self):
        for record in self:
            print (record.env.context, '111111111', record.env.user.company_id.name)
            curr_company = record.env.user.company_id

            print (curr_company.currency_id.name, 'curreeeeeeeeee')
            total = 0.0
            due = 0.0
            rec_rate = record.currency_id.rate
            ctx={}
            ctx['date'] = record.invoice_date

            if record.currency_id:
                # total = self.env['res.currency']._compute(record.currency_id,self.env.user.company_id.currency_id,record.amount_total)
                total = self.env['res.currency']._convert(record.amount_total, self.env.user.company_id.currency_id,
                                                            self.env.user.company_id, record.invoice_date
                                                            )
                # due = self.env['res.currency']._compute(record.currency_id,self.env.user.company_id.currency_id,record.amount_residual)
                due = self.env['res.currency']._convert(record.amount_residual, self.env.user.company_id.currency_id,
                                                          self.env.user.company_id, record.invoice_date
                                                          )


            record.total_local = total or 0.0
            record.due_local = due or 0.0


